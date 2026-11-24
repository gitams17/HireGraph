from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from applications.models import Application, ApplicationEvent, ApplicationStage
from candidates.models import Candidate
from jobs.models import EmploymentType, JobRequisition, JobStatus
from organizations.models import Organization, OrganizationMembership, OrganizationRole
from .models import (
    Interview,
    InterviewFeedback,
    InterviewNotification,
    InterviewParticipant,
    InterviewStatus,
    InterviewType,
    ParticipantRole,
    ParticipantStatus,
    Recommendation,
)

User = get_user_model()


class InterviewManagementTests(APITestCase):
    def setUp(self):
        # Primary Org (Alpha Corp)
        self.org_alpha = Organization.objects.create(name="Alpha Corp", slug="alpha-corp")

        self.recruiter = User.objects.create_user(
            email="recruiter@alpha.com",
            password="StrongPassword123!",
            first_name="Rachel",
            last_name="Recruiter",
        )
        self.interviewer_1 = User.objects.create_user(
            email="tech.lead@alpha.com",
            password="StrongPassword123!",
            first_name="Tom",
            last_name="TechLead",
        )
        self.interviewer_2 = User.objects.create_user(
            email="engineer@alpha.com",
            password="StrongPassword123!",
            first_name="Emma",
            last_name="Engineer",
        )
        self.unassigned_interviewer = User.objects.create_user(
            email="unassigned@alpha.com",
            password="StrongPassword123!",
            first_name="Uma",
            last_name="Unassigned",
        )

        OrganizationMembership.objects.create(
            user=self.recruiter,
            organization=self.org_alpha,
            role=OrganizationRole.RECRUITER,
        )
        OrganizationMembership.objects.create(
            user=self.interviewer_1,
            organization=self.org_alpha,
            role=OrganizationRole.INTERVIEWER,
        )
        OrganizationMembership.objects.create(
            user=self.interviewer_2,
            organization=self.org_alpha,
            role=OrganizationRole.INTERVIEWER,
        )
        OrganizationMembership.objects.create(
            user=self.unassigned_interviewer,
            organization=self.org_alpha,
            role=OrganizationRole.INTERVIEWER,
        )

        # Job and Candidate in Org Alpha
        self.job = JobRequisition.objects.create(
            organization=self.org_alpha,
            title="Senior Backend Engineer",
            department="Core Infrastructure",
            location="Remote",
            employment_type=EmploymentType.FULL_TIME,
            experience_min=4,
            experience_max=8,
            required_skills=["Python", "Django", "PostgreSQL", "Docker"],
            responsibilities=["Scale core APIs", "Design database architecture"],
            status=JobStatus.OPEN,
            created_by=self.recruiter,
        )
        self.candidate = Candidate.objects.create(
            organization=self.org_alpha,
            first_name="Carlos",
            last_name="Mendoza",
            email="carlos.mendoza@example.com",
            current_company="CloudScale Systems",
            current_title="Backend Developer",
            total_experience_years=6,
        )
        self.application = Application.objects.create(
            organization=self.org_alpha,
            job=self.job,
            candidate=self.candidate,
            stage=ApplicationStage.SHORTLISTED,
            created_by=self.recruiter,
        )

        # Org Beta (Tenant Isolation testing)
        self.org_beta = Organization.objects.create(name="Beta Labs", slug="beta-labs")
        self.beta_user = User.objects.create_user(
            email="recruiter@beta.com",
            password="StrongPassword123!",
            first_name="Bob",
            last_name="Beta",
        )
        OrganizationMembership.objects.create(
            user=self.beta_user,
            organization=self.org_beta,
            role=OrganizationRole.RECRUITER,
        )

    def test_schedule_interview_and_assign_multiple_interviewers(self):
        """
        Verify recruiters can schedule an interview, assign multiple interview panel members,
        generate notifications, and advance the application stage.
        """
        self.client.force_authenticate(user=self.recruiter)
        start_time = timezone.now() + timedelta(days=2)
        end_time = start_time + timedelta(hours=1)

        payload = {
            "application_id": str(self.application.id),
            "title": "Technical Round 1: Systems Architecture",
            "interview_type": "technical",
            "scheduled_start": start_time.isoformat(),
            "scheduled_end": end_time.isoformat(),
            "location_type": "remote",
            "meeting_link": "https://meet.google.com/abc-defg-hij",
            "interviewer_ids": [str(self.interviewer_1.id), str(self.interviewer_2.id)],
            "prepared_questions": [
                {"id": "q1", "question": "Explain database connection pooling in Django.", "category": "technical"}
            ],
            "notes": "Focus on concurrency and query optimization.",
        }

        response = self.client.post("/api/v1/interviews/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        interview_id = response.data["id"]
        interview = Interview.objects.get(id=interview_id)
        self.assertEqual(interview.title, "Technical Round 1: Systems Architecture")
        self.assertEqual(interview.status, InterviewStatus.SCHEDULED)

        # Verify participant assignments
        participants = interview.participants.all()
        self.assertEqual(participants.count(), 2)
        assigned_user_ids = {p.user_id for p in participants}
        self.assertIn(self.interviewer_1.id, assigned_user_ids)
        self.assertIn(self.interviewer_2.id, assigned_user_ids)

        # Verify in-app notifications created
        notifications = InterviewNotification.objects.filter(interview=interview)
        self.assertEqual(notifications.count(), 2)

        # Verify application stage transition
        self.application.refresh_from_db()
        self.assertEqual(self.application.stage, ApplicationStage.INTERVIEW)
        self.assertTrue(
            ApplicationEvent.objects.filter(
                application=self.application,
                event_type="stage_changed",
                to_stage=ApplicationStage.INTERVIEW,
            ).exists()
        )

    def test_prevent_invalid_scheduling_end_before_start(self):
        """End time before or equal to start time must fail with 400."""
        self.client.force_authenticate(user=self.recruiter)
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time - timedelta(minutes=30)  # Invalid

        payload = {
            "application_id": str(self.application.id),
            "title": "Invalid Interview",
            "scheduled_start": start_time.isoformat(),
            "scheduled_end": end_time.isoformat(),
        }

        response = self.client.post("/api/v1/interviews/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("scheduled_end", response.data)

    def test_prevent_scheduling_with_non_member_interviewer(self):
        """Assigning a user who is not a member of the organisation must fail."""
        self.client.force_authenticate(user=self.recruiter)
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        payload = {
            "application_id": str(self.application.id),
            "title": "Panel with External User",
            "scheduled_start": start_time.isoformat(),
            "scheduled_end": end_time.isoformat(),
            "interviewer_ids": [str(self.beta_user.id)],  # User belongs to Beta Labs, not Alpha Corp
        }

        response = self.client.post("/api/v1/interviews/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("interviewer_ids", response.data)

    def test_interviewer_can_submit_and_update_feedback(self):
        """Assigned interviewer can submit rating and qualitative evaluation."""
        start_time = timezone.now() + timedelta(hours=3)
        end_time = start_time + timedelta(hours=1)

        interview = Interview.objects.create(
            organization=self.org_alpha,
            application=self.application,
            title="Live Coding Assessment",
            scheduled_start=start_time,
            scheduled_end=end_time,
            created_by=self.recruiter,
        )
        InterviewParticipant.objects.create(
            interview=interview,
            user=self.interviewer_1,
            role=ParticipantRole.INTERVIEWER,
            status=ParticipantStatus.ACCEPTED,
        )

        self.client.force_authenticate(user=self.interviewer_1)

        feedback_payload = {
            "rating": 5,
            "recommendation": Recommendation.STRONG_HIRE,
            "summary": "Outstanding systems problem solving and clean Python coding.",
            "strengths": "Deep knowledge of ACID transactions and PostgreSQL vacuuming.",
            "areas_for_improvement": "Minor: could write docstrings more consistently.",
            "question_scores": [
                {"question_id": "q1", "score": 5, "notes": "Flawless explanation."}
            ],
        }

        # Submit feedback
        url = f"/api/v1/interviews/{interview.id}/feedback/"
        response = self.client.post(url, feedback_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data["rating"], 5)
        self.assertEqual(response.data["recommendation"], Recommendation.STRONG_HIRE)

        # Re-submit feedback (update)
        feedback_payload["summary"] = "Updated: Confirmed excellent team collaboration skills."
        update_response = self.client.post(url, feedback_payload, format="json")
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(InterviewFeedback.objects.filter(interview=interview).count(), 1)
        self.assertEqual(
            InterviewFeedback.objects.get(interview=interview).summary,
            "Updated: Confirmed excellent team collaboration skills.",
        )

        # GET feedback list
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_response.data), 1)

    def test_unassigned_non_manager_cannot_submit_feedback(self):
        """An interviewer who is not assigned to this interview cannot submit feedback."""
        start_time = timezone.now() + timedelta(hours=3)
        end_time = start_time + timedelta(hours=1)

        interview = Interview.objects.create(
            organization=self.org_alpha,
            application=self.application,
            title="Live Coding Assessment",
            scheduled_start=start_time,
            scheduled_end=end_time,
            created_by=self.recruiter,
        )
        # interviewer_1 is assigned, unassigned_interviewer is NOT
        InterviewParticipant.objects.create(
            interview=interview,
            user=self.interviewer_1,
            role=ParticipantRole.INTERVIEWER,
        )

        self.client.force_authenticate(user=self.unassigned_interviewer)
        url = f"/api/v1/interviews/{interview.id}/feedback/"
        response = self.client.post(
            url,
            {"rating": 4, "recommendation": "hire", "summary": "Unassigned attempt."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_organization_isolation(self):
        """Users in Org Beta cannot see or modify interviews in Org Alpha."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        interview = Interview.objects.create(
            organization=self.org_alpha,
            application=self.application,
            title="Confidential Interview Alpha",
            scheduled_start=start_time,
            scheduled_end=end_time,
            created_by=self.recruiter,
        )

        self.client.force_authenticate(user=self.beta_user)

        # Try to retrieve Alpha interview
        detail_response = self.client.get(f"/api/v1/interviews/{interview.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_404_NOT_FOUND)

        # Try to schedule interview for Alpha application
        create_response = self.client.post(
            "/api/v1/interviews/",
            {
                "application_id": str(self.application.id),
                "title": "Breach Attempt",
                "scheduled_start": start_time.isoformat(),
                "scheduled_end": end_time.isoformat(),
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_transitions_and_updates(self):
        """Updating status to completed or rescheduled works properly."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        interview = Interview.objects.create(
            organization=self.org_alpha,
            application=self.application,
            title="Round 2 Interview",
            scheduled_start=start_time,
            scheduled_end=end_time,
            created_by=self.recruiter,
        )
        InterviewParticipant.objects.create(
            interview=interview,
            user=self.interviewer_1,
            role=ParticipantRole.INTERVIEWER,
        )

        self.client.force_authenticate(user=self.recruiter)
        url = f"/api/v1/interviews/{interview.id}/"

        patch_response = self.client.patch(
            url,
            {"status": InterviewStatus.COMPLETED, "notes": "Completed with all panel present."},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        interview.refresh_from_db()
        self.assertEqual(interview.status, InterviewStatus.COMPLETED)
        self.assertEqual(interview.notes, "Completed with all panel present.")

    def test_ai_question_generation_endpoint(self):
        """AI Interview Assistant suggests structured, categorized interview questions."""
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        interview = Interview.objects.create(
            organization=self.org_alpha,
            application=self.application,
            title="Technical Screen",
            interview_type=InterviewType.TECHNICAL,
            scheduled_start=start_time,
            scheduled_end=end_time,
            created_by=self.recruiter,
        )

        self.client.force_authenticate(user=self.interviewer_1)
        url = f"/api/v1/interviews/{interview.id}/generate-questions/"
        response = self.client.post(
            url,
            {"focus_areas": ["PostgreSQL", "Scalability"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("technical_questions", response.data)
        self.assertIn("behavioural_questions", response.data)
        self.assertIn("project_questions", response.data)
        self.assertIn("competency_questions", response.data)
        self.assertTrue(len(response.data["technical_questions"]) > 0)
