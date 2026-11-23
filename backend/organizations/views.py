"""
Organisation API views.

All views require authentication.  Organisation-level gating is applied
inline rather than via DRF permission classes so that failed checks return
404 (not 403) when the caller should not even know the resource exists.
"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    INVITE_ROLES,
    MANAGEMENT_ROLES,
    Organization,
    OrganizationMembership,
    OrganizationRole,
)
from .permissions import get_membership
from .serializers import (
    InvitationCreateSerializer,
    InvitationSerializer,
    MembershipSerializer,
    MembershipUpdateSerializer,
    OrganizationCreateSerializer,
    OrganizationSerializer,
)

_NOT_MEMBER = {"detail": "Not found or you are not a member of this organisation."}
_NO_PERMISSION = {"detail": "You do not have permission to perform this action."}


# ---------------------------------------------------------------------------
# Organisations
# ---------------------------------------------------------------------------


class OrganizationListCreateView(APIView):
    """
    GET   /api/v1/organizations/   – list the caller's organisations.
    POST  /api/v1/organizations/   – create a new organisation; caller → Owner.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        org_ids = OrganizationMembership.objects.filter(
            user=request.user, is_active=True
        ).values_list("organization_id", flat=True)
        orgs = Organization.objects.filter(id__in=org_ids)
        serializer = OrganizationSerializer(orgs, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        serializer = OrganizationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        org = serializer.save(created_by=request.user)
        OrganizationMembership.objects.create(
            organization=org,
            user=request.user,
            role=OrganizationRole.OWNER,
        )
        return Response(
            OrganizationSerializer(org, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationDetailView(APIView):
    """
    GET  /api/v1/organizations/{id}/  – organisation details (members only).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, org_id):
        org = get_object_or_404(Organization, id=org_id)
        if not get_membership(request.user, org):
            return Response(_NOT_MEMBER, status=status.HTTP_404_NOT_FOUND)
        return Response(OrganizationSerializer(org, context={"request": request}).data)


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


class MemberListView(APIView):
    """
    GET  /api/v1/organizations/{id}/members/  – active members (members only).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, org_id):
        org = get_object_or_404(Organization, id=org_id)
        if not get_membership(request.user, org):
            return Response(_NOT_MEMBER, status=status.HTTP_404_NOT_FOUND)
        members = (
            OrganizationMembership.objects
            .filter(organization=org, is_active=True)
            .select_related("user")
        )
        return Response(MembershipSerializer(members, many=True).data)


class MemberDetailView(APIView):
    """
    PATCH /api/v1/organizations/{id}/members/{member_id}/
    Update a member's role or active status (admins/owners only).
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, org_id, member_id):
        org = get_object_or_404(Organization, id=org_id)
        requester = get_membership(request.user, org)

        if not requester or requester.role not in MANAGEMENT_ROLES:
            return Response(_NO_PERMISSION, status=status.HTTP_403_FORBIDDEN)

        target = get_object_or_404(OrganizationMembership, id=member_id, organization=org)

        # Non-owners cannot touch an owner's membership.
        if (
            target.role == OrganizationRole.OWNER
            and requester.role != OrganizationRole.OWNER
        ):
            return Response(
                {"detail": "Only the Owner can modify another Owner's membership."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Only owners can promote someone to Owner.
        new_role = request.data.get("role")
        if new_role == OrganizationRole.OWNER and requester.role != OrganizationRole.OWNER:
            return Response(
                {"detail": "Only the Owner can assign the Owner role."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = MembershipUpdateSerializer(target, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MembershipSerializer(target).data)


# ---------------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------------


class InvitationListCreateView(APIView):
    """
    GET   /api/v1/organizations/{id}/invitations/  – list invitations (admins+).
    POST  /api/v1/organizations/{id}/invitations/  – invite a member (admins/recruiters+).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, org_id):
        org = get_object_or_404(Organization, id=org_id)
        requester = get_membership(request.user, org)
        if not requester or requester.role not in MANAGEMENT_ROLES:
            return Response(_NO_PERMISSION, status=status.HTTP_403_FORBIDDEN)
        invitations = org.invitations.select_related("invited_by")
        return Response(InvitationSerializer(invitations, many=True).data)

    def post(self, request, org_id):
        org = get_object_or_404(Organization, id=org_id)
        requester = get_membership(request.user, org)
        if not requester or requester.role not in INVITE_ROLES:
            return Response(_NO_PERMISSION, status=status.HTTP_403_FORBIDDEN)

        serializer = InvitationCreateSerializer(
            data=request.data,
            context={"organization": org, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save(organization=org, invited_by=request.user)
        return Response(
            InvitationSerializer(invitation).data, status=status.HTTP_201_CREATED
        )
