from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from candidates.models import Candidate
from jobs.models import EmploymentType, JobRequisition, JobStatus
from organizations.models import Organization, OrganizationMembership, OrganizationRole
from .models import Application, ApplicationEvent, ApplicationStage

User = get_user_model()


class ApplicationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="recruiter@example.com",
            password="StrongPassword123!",
            first_name="Sarah",
            last_name="Recruiter",
        )
        self.hiring_manager = User.objects.create_user(
            email="manager@example.com",
            password="StrongPassword123!",
            first_name="Marcus",
            last_name="Manager",
        )
        self.org = Organization.objects.create(name="Alpha Ventures", slug="alpha-ventures")

        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org,
            role=OrganizationRole.RECRUITER,
        )
        OrganizationMembership.objects.create(
            user=self.hiring_manager,
            organization=self.org,
            role=OrganizationRole.HIRING_MANAGER,
        )

        # Create Job and Candidate
        self.job = JobRequisition.objects.create(
            organization=self.org,
            title="Senior Python Developer",
            department="Engineering",
            location="Remote",
            employment_type=EmploymentType.FULL_TIME,
            status=JobStatus.OPEN,
            created_by=self.user,
        )
        self.candidate = Candidate.objects.create(
            organization=self.org,
            first_name="Alex",
            last_name="Rivera",
            email="alex.rivera@example.com",
            current_company="Acme Cloud",
            current_title="Software Engineer",
            total_experience_years=5,
        )

        # Other org & user
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
            first_name="Other",
            last_name="Person",
        )
        self.other_org = Organization.objects.create(name="Beta Corp", slug="beta-corp")
        OrganizationMembership.objects.create(
            user=self.other_user,
            organization=self.other_org,
            role=OrganizationRole.RECRUITER,
        )

        self.client.force_authenticate(user=self.user)

    def test_create_application(self):
        payload = {
            "job_id": str(self.job.id),
            "candidate_id": str(self.candidate.id),
            "notes": "Strong candidate referral.",
        }
        res = self.client.post("/api/v1/applications/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["stage"], ApplicationStage.APPLIED)

        # Check ApplicationEvent created
        app_id = res.data["id"]
        app = Application.objects.get(id=app_id)
        events = app.events.all()
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first().event_type, "created")

    def test_prevent_duplicate_application(self):
        # First application succeeds
        payload = {
            "job_id": str(self.job.id),
            "candidate_id": str(self.candidate.id),
        }
        res1 = self.client.post("/api/v1/applications/", payload, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Duplicate application rejected
        res2 = self.client.post("/api/v1/applications/", payload, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", res2.data)

    def test_cross_org_application_rejected(self):
        other_candidate = Candidate.objects.create(
            organization=self.other_org,
            first_name="Cross",
            last_name="Org",
            email="cross@other.com",
        )
        payload = {
            "job_id": str(self.job.id),
            "candidate_id": str(other_candidate.id),
        }
        res = self.client.post("/api/v1/applications/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_application_stage_transitions(self):
        app = Application.objects.create(
            organization=self.org,
            job=self.job,
            candidate=self.candidate,
            stage=ApplicationStage.APPLIED,
            created_by=self.user,
        )

        # Recruiter moves to under_review
        res1 = self.client.patch(
            f"/api/v1/applications/{app.id}/stage/",
            {"stage": ApplicationStage.UNDER_REVIEW, "notes": "Profile meets requirements."},
            format="json",
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data["stage"], ApplicationStage.UNDER_REVIEW)

        # Hiring manager moves to interview with rating
        self.client.force_authenticate(user=self.hiring_manager)
        res2 = self.client.patch(
            f"/api/v1/applications/{app.id}/stage/",
            {
                "stage": ApplicationStage.INTERVIEW,
                "notes": "Scheduled technical screen.",
                "rating": 4,
            },
            format="json",
        )
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["stage"], ApplicationStage.INTERVIEW)
        self.assertEqual(res2.data["rating"], 4)

        # Verify audit history
        app.refresh_from_db()
        self.assertEqual(app.stage, ApplicationStage.INTERVIEW)
        events = list(app.events.all())
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].from_stage, ApplicationStage.APPLIED)
        self.assertEqual(events[0].to_stage, ApplicationStage.UNDER_REVIEW)
        self.assertEqual(events[1].from_stage, ApplicationStage.UNDER_REVIEW)
        self.assertEqual(events[1].to_stage, ApplicationStage.INTERVIEW)
        self.assertEqual(events[1].actor, self.hiring_manager)

    def test_application_org_isolation(self):
        app = Application.objects.create(
            organization=self.org,
            job=self.job,
            candidate=self.candidate,
            stage=ApplicationStage.APPLIED,
            created_by=self.user,
        )

        self.client.force_authenticate(user=self.other_user)
        res = self.client.get(f"/api/v1/applications/{app.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
