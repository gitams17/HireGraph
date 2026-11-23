"""
Organisation models.

Organization       – a hiring company / team.
OrganizationMembership – links users to organisations with a role.
OrganizationInvitation – email invitation with a unique token.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_organizations",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    # ------------------------------------------------------------------
    # Slug generation
    # ------------------------------------------------------------------

    def _unique_slug(self) -> str:
        base = slugify(self.name) or "org"
        slug = base
        n = 1
        qs = Organization.objects.exclude(pk=self.pk)
        while qs.filter(slug=slug).exists():
            slug = f"{base}-{n}"
            n += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


class OrganizationRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    RECRUITER = "recruiter", "Recruiter"
    HIRING_MANAGER = "hiring_manager", "Hiring Manager"
    INTERVIEWER = "interviewer", "Interviewer"


# Role sets used by permission helpers.
MANAGEMENT_ROLES = frozenset({OrganizationRole.OWNER, OrganizationRole.ADMIN})
INVITE_ROLES = frozenset(
    {OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.RECRUITER}
)


# ---------------------------------------------------------------------------
# Membership
# ---------------------------------------------------------------------------


class OrganizationMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=30,
        choices=OrganizationRole.choices,
        default=OrganizationRole.INTERVIEWER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("organization", "user")]
        ordering = ["joined_at"]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.organization.name} ({self.role})"


# ---------------------------------------------------------------------------
# Invitation
# ---------------------------------------------------------------------------


class OrganizationInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField()
    role = models.CharField(
        max_length=30,
        choices=OrganizationRole.choices,
        default=OrganizationRole.RECRUITER,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        # Prevent duplicate active invitations; expired ones are allowed
        # to be re-sent — that check is handled at the serializer level.
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Invitation for {self.email} → {self.organization.name}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_accepted(self) -> bool:
        return self.accepted_at is not None
