"""
Tests for ApprovalRequest API & Permissions.
- Owner, Admin, Hiring Manager can approve/reject.
- Recruiter, Interviewer, and Non-members cannot approve/reject.
- Double-decision prevention (cannot decide an already approved/rejected request).
- Cross-organization isolation.
"""

import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from approvals.models import ApprovalRequest, ApprovalStatus
from jobs.models import JobDescriptionVersion, JobRequisition
from organizations.models import Organization, OrganizationMembership


def make_user(email: str) -> User:
    return User.objects.create_user(email=email, password="password123!", first_name="Test", last_name="User")


def make_org(name: str, owner: User) -> Organization:
    org = Organization.objects.create(name=name, slug=name.lower().replace(" ", "-"), created_by=owner)
    OrganizationMembership.objects.create(organization=org, user=owner, role="owner", is_active=True)
    return org


def add_member(org: Organization, user: User, role: str) -> OrganizationMembership:
    return OrganizationMembership.objects.create(organization=org, user=user, role=role, is_active=True)


class ApprovalRequestTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner@approvals.com")
        self.hm = make_user("hm@approvals.com")
        self.recruiter = make_user("recruiter@approvals.com")
        self.interviewer = make_user("interviewer@approvals.com")
        self.outsider = make_user("outsider@approvals.com")

        self.org = make_org("Approvals Org", self.owner)
        add_member(self.org, self.hm, "hiring_manager")
        add_member(self.org, self.recruiter, "recruiter")
        add_member(self.org, self.interviewer, "interviewer")

        self.job = JobRequisition.objects.create(
            organization=self.org,
            title="Senior Platform Engineer",
            department="Infrastructure",
            created_by=self.owner,
        )

        self.version = JobDescriptionVersion.objects.create(
            job=self.job,
            version_number=1,
            title=self.job.title,
            overview="Great role.",
            responsibilities=["Maintain k8s"],
            required_qualifications=["Go", "Kubernetes"],
            status="pending_approval",
            created_by=self.recruiter,
        )

        self.approval = ApprovalRequest.objects.create(
            organization=self.org,
            job=self.job,
            version=self.version,
            requested_by=self.recruiter,
            status=ApprovalStatus.PENDING,
        )

    def test_list_approvals_as_member(self):
        self.client.force_authenticate(self.recruiter)
        resp = self.client.get("/api/v1/approvals/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data.get("results", resp.data)), 1)

    def test_list_approvals_excludes_outsider(self):
        self.client.force_authenticate(self.outsider)
        resp = self.client.get("/api/v1/approvals/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data.get("results", resp.data)), 0)

    def test_hiring_manager_can_approve(self):
        self.client.force_authenticate(self.hm)
        url = f"/api/v1/approvals/{self.approval.id}/decide/"
        resp = self.client.post(url, {"action": "approve", "feedback": "Looks fantastic!"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, ApprovalStatus.APPROVED)
        self.assertEqual(self.approval.reviewed_by, self.hm)
        self.assertEqual(self.approval.feedback, "Looks fantastic!")

    def test_owner_can_reject_with_feedback(self):
        self.client.force_authenticate(self.owner)
        url = f"/api/v1/approvals/{self.approval.id}/decide/"
        resp = self.client.post(url, {"action": "reject", "feedback": "Needs higher salary range and cloud experience."}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, ApprovalStatus.REJECTED)
        self.assertEqual(self.approval.feedback, "Needs higher salary range and cloud experience.")

    def test_recruiter_cannot_decide_approval(self):
        self.client.force_authenticate(self.recruiter)
        url = f"/api/v1/approvals/{self.approval.id}/decide/"
        resp = self.client.post(url, {"action": "approve"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_interviewer_cannot_decide_approval(self):
        self.client.force_authenticate(self.interviewer)
        url = f"/api/v1/approvals/{self.approval.id}/decide/"
        resp = self.client.post(url, {"action": "approve"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_approval_rejected(self):
        self.client.force_authenticate(self.hm)
        url = f"/api/v1/approvals/{self.approval.id}/decide/"
        # First decision
        resp1 = self.client.post(url, {"action": "approve"}, format="json")
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        # Duplicate decision attempt
        resp2 = self.client.post(url, {"action": "approve"}, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", resp2.data)
