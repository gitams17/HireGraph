"""
Organisations test suite.

Covers:
  - Create organisation (success, slug generation, unauthenticated)
  - List organisations (own only, not other users')
  - Organisation detail (member sees it, non-member gets 404)
  - Member list (member OK, outsider 404)
  - Update member role (owner OK, non-manager 403)
  - Invite member (admin OK, duplicate rejected, already-member rejected)
  - Cross-organisation data isolation
"""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Organization, OrganizationMembership, OrganizationRole

User = get_user_model()

ORGS_URL = "/api/v1/organizations/"


def org_detail_url(org_id: str) -> str:
    return f"/api/v1/organizations/{org_id}/"


def members_url(org_id: str) -> str:
    return f"/api/v1/organizations/{org_id}/members/"


def member_detail_url(org_id: str, member_id: str) -> str:
    return f"/api/v1/organizations/{org_id}/members/{member_id}/"


def invitations_url(org_id: str) -> str:
    return f"/api/v1/organizations/{org_id}/invitations/"


def create_user(**kwargs):
    defaults = {"password": "securepassword1", "first_name": "T", "last_name": "U"}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


# ---------------------------------------------------------------------------
# Organisation creation
# ---------------------------------------------------------------------------


class OrganizationCreateTests(APITestCase):
    def setUp(self):
        self.alice = create_user(email="alice@example.com")
        self.client.force_login(self.alice)

    def test_create_org_returns_201(self):
        response = self.client.post(ORGS_URL, {"name": "Acme Corp"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_org_caller_becomes_owner(self):
        self.client.post(ORGS_URL, {"name": "Acme Corp"}, format="json")
        org = Organization.objects.get(name="Acme Corp")
        m = OrganizationMembership.objects.get(organization=org, user=self.alice)
        self.assertEqual(m.role, OrganizationRole.OWNER)

    def test_create_org_generates_slug(self):
        resp = self.client.post(ORGS_URL, {"name": "My Great Company"}, format="json")
        self.assertEqual(resp.data["slug"], "my-great-company")

    def test_create_org_slug_collision_increments(self):
        self.client.post(ORGS_URL, {"name": "Duplicate"}, format="json")
        resp = self.client.post(ORGS_URL, {"name": "Duplicate"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["slug"], "duplicate-1")

    def test_create_org_unauthenticated_returns_403(self):
        self.client.logout()
        response = self.client.post(ORGS_URL, {"name": "Secret"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# List / detail
# ---------------------------------------------------------------------------


class OrganizationListDetailTests(APITestCase):
    def setUp(self):
        self.alice = create_user(email="alice@example.com")
        self.bob = create_user(email="bob@example.com")

    def test_list_returns_only_own_orgs(self):
        self.client.force_login(self.alice)
        self.client.post(ORGS_URL, {"name": "Alice Org"}, format="json")
        self.client.force_login(self.bob)
        self.client.post(ORGS_URL, {"name": "Bob Org"}, format="json")

        self.client.force_login(self.alice)
        response = self.client.get(ORGS_URL)
        names = [o["name"] for o in response.data]
        self.assertIn("Alice Org", names)
        self.assertNotIn("Bob Org", names)

    def test_detail_member_sees_org(self):
        self.client.force_login(self.alice)
        resp = self.client.post(ORGS_URL, {"name": "Alpha"}, format="json")
        org_id = resp.data["id"]
        detail = self.client.get(org_detail_url(org_id))
        self.assertEqual(detail.status_code, status.HTTP_200_OK)

    def test_detail_outsider_gets_404(self):
        self.client.force_login(self.alice)
        resp = self.client.post(ORGS_URL, {"name": "Alpha"}, format="json")
        org_id = resp.data["id"]

        self.client.force_login(self.bob)
        detail = self.client.get(org_detail_url(org_id))
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Member management
# ---------------------------------------------------------------------------


class MemberTests(APITestCase):
    def setUp(self):
        self.owner = create_user(email="owner@example.com")
        self.recruiter = create_user(email="recruiter@example.com")
        self.outsider = create_user(email="outsider@example.com")

        self.client.force_login(self.owner)
        resp = self.client.post(ORGS_URL, {"name": "Corp"}, format="json")
        self.org_id = resp.data["id"]
        self.org = Organization.objects.get(id=self.org_id)

        self.recruiter_membership = OrganizationMembership.objects.create(
            organization=self.org, user=self.recruiter, role=OrganizationRole.RECRUITER
        )

    def test_owner_lists_all_members(self):
        self.client.force_login(self.owner)
        resp = self.client.get(members_url(self.org_id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)  # owner + recruiter

    def test_outsider_gets_404_on_member_list(self):
        self.client.force_login(self.outsider)
        resp = self.client.get(members_url(self.org_id))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_change_member_role(self):
        self.client.force_login(self.owner)
        url = member_detail_url(self.org_id, str(self.recruiter_membership.id))
        resp = self.client.patch(url, {"role": "hiring_manager"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.recruiter_membership.refresh_from_db()
        self.assertEqual(self.recruiter_membership.role, OrganizationRole.HIRING_MANAGER)

    def test_recruiter_cannot_change_roles(self):
        self.client.force_login(self.recruiter)
        url = member_detail_url(self.org_id, str(self.recruiter_membership.id))
        resp = self.client.patch(url, {"role": "interviewer"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_promote_to_owner(self):
        admin_user = create_user(email="admin@example.com")
        admin_m = OrganizationMembership.objects.create(
            organization=self.org, user=admin_user, role=OrganizationRole.ADMIN
        )
        self.client.force_login(admin_user)
        url = member_detail_url(self.org_id, str(self.recruiter_membership.id))
        resp = self.client.patch(url, {"role": "owner"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_cross_org_member_patch_blocked(self):
        """A user cannot patch a membership that belongs to a different org."""
        self.client.force_login(self.outsider)
        resp = self.client.post(ORGS_URL, {"name": "Outsider Org"}, format="json")
        # Outsider tries to patch a membership in the other org
        url = member_detail_url(self.org_id, str(self.recruiter_membership.id))
        resp = self.client.patch(url, {"role": "interviewer"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------


class InvitationTests(APITestCase):
    def setUp(self):
        self.owner = create_user(email="owner@example.com")
        self.client.force_login(self.owner)
        resp = self.client.post(ORGS_URL, {"name": "Invite Corp"}, format="json")
        self.org_id = resp.data["id"]
        self.org = Organization.objects.get(id=self.org_id)

    def test_owner_can_invite(self):
        resp = self.client.post(
            invitations_url(self.org_id),
            {"email": "new@example.com", "role": "recruiter"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["email"], "new@example.com")

    def test_duplicate_active_invitation_rejected(self):
        self.client.post(
            invitations_url(self.org_id),
            {"email": "dup@example.com", "role": "recruiter"},
            format="json",
        )
        resp = self.client.post(
            invitations_url(self.org_id),
            {"email": "dup@example.com", "role": "recruiter"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inviting_existing_member_rejected(self):
        member = create_user(email="member@example.com")
        OrganizationMembership.objects.create(
            organization=self.org, user=member, role=OrganizationRole.INTERVIEWER
        )
        resp = self.client.post(
            invitations_url(self.org_id),
            {"email": "member@example.com", "role": "recruiter"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_cannot_invite(self):
        outsider = create_user(email="outsider@example.com")
        self.client.force_login(outsider)
        resp = self.client.post(
            invitations_url(self.org_id),
            {"email": "someone@example.com", "role": "recruiter"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
