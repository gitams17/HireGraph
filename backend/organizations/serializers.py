from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import (
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
)

User = get_user_model()

# ---------------------------------------------------------------------------
# Organisation
# ---------------------------------------------------------------------------


class OrganizationSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    # Include the calling user's role for convenience.
    current_user_role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "created_at",
            "updated_at",
            "created_by",
            "member_count",
            "current_user_role",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at", "created_by"]

    def get_member_count(self, obj) -> int:
        return obj.memberships.filter(is_active=True).count()

    def get_current_user_role(self, obj) -> str | None:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        m = obj.memberships.filter(user=request.user, is_active=True).first()
        return m.role if m else None


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["name"]


# ---------------------------------------------------------------------------
# Membership
# ---------------------------------------------------------------------------


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = ["id", "user", "role", "joined_at", "is_active"]
        read_only_fields = ["id", "user", "joined_at"]


class MembershipUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMembership
        fields = ["role", "is_active"]


# ---------------------------------------------------------------------------
# Invitation
# ---------------------------------------------------------------------------


class InvitationSerializer(serializers.ModelSerializer):
    invited_by = UserSerializer(read_only=True)
    is_expired = serializers.ReadOnlyField()
    is_accepted = serializers.ReadOnlyField()

    class Meta:
        model = OrganizationInvitation
        fields = [
            "id",
            "email",
            "role",
            "invited_by",
            "token",
            "created_at",
            "accepted_at",
            "expires_at",
            "is_expired",
            "is_accepted",
        ]
        read_only_fields = [
            "id",
            "token",
            "invited_by",
            "created_at",
            "accepted_at",
            "expires_at",
        ]


class InvitationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationInvitation
        fields = ["email", "role"]

    def validate_email(self, value: str) -> str:
        return value.lower()

    def validate(self, attrs: dict) -> dict:
        organization = self.context["organization"]
        email = attrs["email"]

        # Reject if the email already belongs to an active member.
        try:
            existing_user = User.objects.get(email=email)
            if OrganizationMembership.objects.filter(
                organization=organization, user=existing_user, is_active=True
            ).exists():
                raise serializers.ValidationError(
                    {"email": "This user is already a member of the organisation."}
                )
        except User.DoesNotExist:
            pass

        # Reject if there is a non-expired, non-accepted invitation.
        if OrganizationInvitation.objects.filter(
            organization=organization,
            email=email,
            accepted_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).exists():
            raise serializers.ValidationError(
                {"email": "An active invitation already exists for this email address."}
            )

        return attrs

    def create(self, validated_data: dict) -> OrganizationInvitation:
        return OrganizationInvitation.objects.create(
            expires_at=timezone.now() + timedelta(days=7),
            **validated_data,
        )
