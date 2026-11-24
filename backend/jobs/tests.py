"""
Comprehensive tests for the jobs app.

Test groups:
1. JobRequisitionCreateTests      - POST /api/v1/jobs/
2. JobRequisitionListTests        - GET  /api/v1/jobs/
3. JobRequisitionDetailTests      - GET  /api/v1/jobs/{id}/
4. JobRequisitionUpdateTests      - PATCH /api/v1/jobs/{id}/
5. JobRequisitionDeleteTests      - DELETE /api/v1/jobs/{id}/
6. JobRequisitionFilterTests      - Query param filtering + search
7. JobRequisitionIsolationTests   - Cross-organisation data isolation
"""

import uuid

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from organizations.models import Organization, OrganizationMembership

from .models import JobRequisition, JobStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email: str, password: str = "testpass123!") -> User:
    return User.objects.create_user(
        email=email,
        password=password,
        first_name="Test",
        last_name="User",
    )


def make_org(name: str, owner: User) -> Organization:
    org = Organization.objects.create(
        name=name,
        slug=name.lower().replace(" ", "-"),
        created_by=owner,
    )
    OrganizationMembership.objects.create(
        organization=org,
        user=owner,
        role="owner",
        is_active=True,
    )
    return org


def add_member(org: Organization, user: User, role: str) -> OrganizationMembership:
    return OrganizationMembership.objects.create(
        organization=org,
        user=user,
        role=role,
        is_active=True,
    )


JOBS_LIST_URL = "/api/v1/jobs/"


def job_detail_url(job_id) -> str:
    return f"/api/v1/jobs/{job_id}/"


VALID_JOB_PAYLOAD = {
    "title": "Senior Backend Engineer",
    "department": "Engineering",
    "location": "Remote",
    "employment_type": "full_time",
    "experience_min": 3,
    "experience_max": 7,
    "required_skills": ["Python", "Django", "PostgreSQL"],
    "responsibilities": ["Design APIs", "Code review"],
    "status": "draft",
}


# ---------------------------------------------------------------------------
# 1. Create Tests
# ---------------------------------------------------------------------------

class JobRequisitionCreateTests(APITestCase):

    def setUp(self):
        self.owner = make_user("owner@example.com")
        self.recruiter = make_user("recruiter@example.com")
        self.hiring_mgr = make_user("hm@example.com")
        self.interviewer = make_user("iv@example.com")
        self.org = make_org("Acme Corp", self.owner)
        add_member(self.org, self.recruiter, "recruiter")
        add_member(self.org, self.hiring_mgr, "hiring_manager")
        add_member(self.org, self.interviewer, "interviewer")

    def _payload(self, **kwargs):
        data = {**VALID_JOB_PAYLOAD, "organization": str(self.org.id)}
        data.update(kwargs)
        return data

    def test_owner_can_create_job(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.post(JOBS_LIST_URL, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["title"], "Senior Backend Engineer")
        self.assertEqual(resp.data["status"], "draft")

    def test_recruiter_can_create_job(self):
        self.client.force_authenticate(self.recruiter)
        resp = self.client.post(JOBS_LIST_URL, self._payload(title="Junior Dev"), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_hiring_manager_cannot_create_job(self):
        self.client.force_authenticate(self.hiring_mgr)
        resp = self.client.post(JOBS_LIST_URL, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_interviewer_cannot_create_job(self):
        self.client.force_authenticate(self.interviewer)
        resp = self.client.post(JOBS_LIST_URL, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create(self):
        resp = self.client.post(JOBS_LIST_URL, self._payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_title_returns_400(self):
        self.client.force_authenticate(self.owner)
        payload = self._payload()
        del payload["title"]
        resp = self.client.post(JOBS_LIST_URL, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", resp.data)

    def test_invalid_experience_range_returns_400(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.post(
            JOBS_LIST_URL,
            self._payload(experience_min=10, experience_max=5),
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_skills_type_returns_400(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.post(
            JOBS_LIST_URL,
            self._payload(required_skills="Python,Django"),  # string instead of list
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_organization_returns_400(self):
        self.client.force_authenticate(self.owner)
        payload = {**VALID_JOB_PAYLOAD}
        resp = self.client.post(JOBS_LIST_URL, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonmember_org_returns_404(self):
        other_user = make_user("outsider@example.com")
        other_org = make_org("Other Corp", other_user)
        self.client.force_authenticate(self.owner)  # owner of Acme, not Other Corp
        resp = self.client.post(
            JOBS_LIST_URL,
            {**VALID_JOB_PAYLOAD, "organization": str(other_org.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_job_created_in_database(self):
        self.client.force_authenticate(self.owner)
        self.client.post(JOBS_LIST_URL, self._payload(), format="json")
        self.assertEqual(JobRequisition.objects.count(), 1)
        job = JobRequisition.objects.first()
        self.assertEqual(job.title, "Senior Backend Engineer")
        self.assertEqual(job.created_by, self.owner)
        self.assertEqual(job.organization, self.org)


# ---------------------------------------------------------------------------
# 2. List Tests
# ---------------------------------------------------------------------------

class JobRequisitionListTests(APITestCase):

    def setUp(self):
        self.owner = make_user("lowner@example.com")
        self.org = make_org("List Corp", self.owner)
        self.client.force_authenticate(self.owner)
        for i in range(3):
            JobRequisition.objects.create(
                organization=self.org,
                title=f"Job {i}",
                created_by=self.owner,
                status="open" if i < 2 else "draft",
            )

    def test_list_returns_paginated_jobs(self):
        resp = self.client.get(JOBS_LIST_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(resp.data["count"], 3)

    def test_unauthenticated_cannot_list(self):
        self.client.logout()
        resp = self.client.get(JOBS_LIST_URL)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_excludes_other_org_jobs(self):
        other_user = make_user("lother@example.com")
        other_org = make_org("Other Corp", other_user)
        JobRequisition.objects.create(
            organization=other_org,
            title="Hidden Job",
            created_by=other_user,
        )
        resp = self.client.get(JOBS_LIST_URL)
        titles = [j["title"] for j in resp.data["results"]]
        self.assertNotIn("Hidden Job", titles)
        self.assertEqual(resp.data["count"], 3)

    def test_hiring_manager_can_list(self):
        hm = make_user("lhm@example.com")
        add_member(self.org, hm, "hiring_manager")
        self.client.force_authenticate(hm)
        resp = self.client.get(JOBS_LIST_URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# 3. Detail Tests
# ---------------------------------------------------------------------------

class JobRequisitionDetailTests(APITestCase):

    def setUp(self):
        self.owner = make_user("downer@example.com")
        self.org = make_org("Detail Corp", self.owner)
        self.job = JobRequisition.objects.create(
            organization=self.org,
            title="Detail Test Job",
            created_by=self.owner,
            required_skills=["Python"],
            responsibilities=["Design"],
        )

    def test_owner_can_retrieve_detail(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.get(job_detail_url(self.job.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "Detail Test Job")
        self.assertIn("required_skills", resp.data)

    def test_nonmember_gets_404(self):
        outsider = make_user("dout@example.com")
        self.client.force_authenticate(outsider)
        resp = self.client.get(job_detail_url(self.job.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_job_returns_404(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.get(job_detail_url(uuid.uuid4()))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# 4. Update Tests
# ---------------------------------------------------------------------------

class JobRequisitionUpdateTests(APITestCase):

    def setUp(self):
        self.owner = make_user("uowner@example.com")
        self.recruiter = make_user("urecruiter@example.com")
        self.hiring_mgr = make_user("uhm@example.com")
        self.org = make_org("Update Corp", self.owner)
        add_member(self.org, self.recruiter, "recruiter")
        add_member(self.org, self.hiring_mgr, "hiring_manager")
        self.job = JobRequisition.objects.create(
            organization=self.org,
            title="Original Title",
            created_by=self.owner,
            status="draft",
        )

    def test_owner_can_patch(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(
            job_detail_url(self.job.id),
            {"title": "Updated Title", "status": "open"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["title"], "Updated Title")
        self.assertEqual(resp.data["status"], "open")

    def test_recruiter_can_patch(self):
        self.client.force_authenticate(self.recruiter)
        resp = self.client.patch(
            job_detail_url(self.job.id),
            {"department": "Engineering"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["department"], "Engineering")

    def test_hiring_manager_cannot_patch(self):
        self.client.force_authenticate(self.hiring_mgr)
        resp = self.client.patch(
            job_detail_url(self.job.id),
            {"title": "Should Fail"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_experience_range_on_patch(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.patch(
            job_detail_url(self.job.id),
            {"experience_min": 8, "experience_max": 2},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_persists_to_database(self):
        self.client.force_authenticate(self.owner)
        self.client.patch(
            job_detail_url(self.job.id),
            {"status": "open"},
            format="json",
        )
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "open")


# ---------------------------------------------------------------------------
# 5. Delete Tests
# ---------------------------------------------------------------------------

class JobRequisitionDeleteTests(APITestCase):

    def setUp(self):
        self.owner = make_user("delowner@example.com")
        self.interviewer = make_user("deliv@example.com")
        self.org = make_org("Delete Corp", self.owner)
        add_member(self.org, self.interviewer, "interviewer")
        self.job = JobRequisition.objects.create(
            organization=self.org,
            title="To Be Deleted",
            created_by=self.owner,
        )

    def test_owner_can_delete(self):
        self.client.force_authenticate(self.owner)
        resp = self.client.delete(job_detail_url(self.job.id))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(JobRequisition.objects.count(), 0)

    def test_interviewer_cannot_delete(self):
        self.client.force_authenticate(self.interviewer)
        resp = self.client.delete(job_detail_url(self.job.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(JobRequisition.objects.count(), 1)

    def test_nonmember_cannot_delete(self):
        outsider = make_user("delout@example.com")
        self.client.force_authenticate(outsider)
        resp = self.client.delete(job_detail_url(self.job.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# 6. Filter and Search Tests
# ---------------------------------------------------------------------------

class JobRequisitionFilterTests(APITestCase):

    def setUp(self):
        self.owner = make_user("fowner@example.com")
        self.org = make_org("Filter Corp", self.owner)
        self.client.force_authenticate(self.owner)

        self.j1 = JobRequisition.objects.create(
            organization=self.org,
            title="Senior Python Developer",
            department="Engineering",
            location="Remote",
            employment_type="full_time",
            status="open",
            created_by=self.owner,
        )
        self.j2 = JobRequisition.objects.create(
            organization=self.org,
            title="Product Manager",
            department="Product",
            location="New York",
            employment_type="full_time",
            status="draft",
            created_by=self.owner,
        )
        self.j3 = JobRequisition.objects.create(
            organization=self.org,
            title="UX Designer",
            department="Design",
            location="Remote",
            employment_type="contract",
            status="open",
            created_by=self.owner,
        )

    def test_filter_by_status_open(self):
        resp = self.client.get(JOBS_LIST_URL, {"status": "open"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 2)
        statuses = {j["status"] for j in resp.data["results"]}
        self.assertEqual(statuses, {"open"})

    def test_filter_by_status_draft(self):
        resp = self.client.get(JOBS_LIST_URL, {"status": "draft"})
        self.assertEqual(resp.data["count"], 1)

    def test_filter_by_department(self):
        resp = self.client.get(JOBS_LIST_URL, {"department": "Engineering"})
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["title"], "Senior Python Developer")

    def test_filter_by_employment_type(self):
        resp = self.client.get(JOBS_LIST_URL, {"employment_type": "contract"})
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["title"], "UX Designer")

    def test_search_by_title(self):
        resp = self.client.get(JOBS_LIST_URL, {"search": "developer"})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["title"], "Senior Python Developer")

    def test_search_by_department(self):
        resp = self.client.get(JOBS_LIST_URL, {"search": "Product"})
        self.assertEqual(resp.data["count"], 1)

    def test_combined_filter_status_and_location(self):
        resp = self.client.get(JOBS_LIST_URL, {"status": "open", "location": "Remote"})
        self.assertEqual(resp.data["count"], 2)

    def test_no_matching_filter_returns_empty(self):
        resp = self.client.get(JOBS_LIST_URL, {"status": "closed"})
        self.assertEqual(resp.data["count"], 0)
        self.assertEqual(resp.data["results"], [])


# ---------------------------------------------------------------------------
# 7. Cross-Organisation Isolation Tests
# ---------------------------------------------------------------------------

class JobRequisitionIsolationTests(APITestCase):

    def setUp(self):
        # Org A
        self.owner_a = make_user("oa@example.com")
        self.org_a = make_org("Org A", self.owner_a)
        self.job_a = JobRequisition.objects.create(
            organization=self.org_a,
            title="Org A Job",
            created_by=self.owner_a,
            status="open",
        )

        # Org B
        self.owner_b = make_user("ob@example.com")
        self.org_b = make_org("Org B", self.owner_b)
        self.job_b = JobRequisition.objects.create(
            organization=self.org_b,
            title="Org B Job",
            created_by=self.owner_b,
            status="open",
        )

    def test_owner_a_cannot_see_org_b_jobs(self):
        self.client.force_authenticate(self.owner_a)
        resp = self.client.get(JOBS_LIST_URL)
        titles = [j["title"] for j in resp.data["results"]]
        self.assertIn("Org A Job", titles)
        self.assertNotIn("Org B Job", titles)

    def test_owner_a_cannot_retrieve_org_b_job(self):
        self.client.force_authenticate(self.owner_a)
        resp = self.client.get(job_detail_url(self.job_b.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_a_cannot_patch_org_b_job(self):
        self.client.force_authenticate(self.owner_a)
        resp = self.client.patch(
            job_detail_url(self.job_b.id),
            {"title": "Hijacked"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_a_cannot_delete_org_b_job(self):
        self.client.force_authenticate(self.owner_a)
        resp = self.client.delete(job_detail_url(self.job_b.id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(JobRequisition.objects.filter(organization=self.org_b).count(), 1)

    def test_owner_a_cannot_create_job_for_org_b(self):
        self.client.force_authenticate(self.owner_a)
        resp = self.client.post(
            JOBS_LIST_URL,
            {**VALID_JOB_PAYLOAD, "organization": str(self.org_b.id)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
