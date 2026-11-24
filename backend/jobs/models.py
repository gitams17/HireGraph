import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class JobStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    OPEN = "open", "Open"
    PAUSED = "paused", "Paused"
    CLOSED = "closed", "Closed"


class EmploymentType(models.TextChoices):
    FULL_TIME = "full_time", "Full-time"
    PART_TIME = "part_time", "Part-time"
    CONTRACT = "contract", "Contract"
    INTERNSHIP = "internship", "Internship"


class JobRequisition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="job_requisitions",
    )
    title = models.CharField(max_length=255)
    department = models.CharField(max_length=100, blank=True, default="")
    location = models.CharField(max_length=100, blank=True, default="")
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    experience_min = models.PositiveIntegerField(null=True, blank=True)
    experience_max = models.PositiveIntegerField(null=True, blank=True)
    required_skills = models.JSONField(default=list, blank=True)
    responsibilities = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=10,
        choices=JobStatus.choices,
        default=JobStatus.DRAFT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_jobs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization"], name="job_org_idx"),
            models.Index(fields=["status"], name="job_status_idx"),
            models.Index(fields=["organization", "status"], name="job_org_status_idx"),
            models.Index(fields=["-created_at"], name="job_created_at_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.organization.name})"

    def clean(self) -> None:
        if (
            self.experience_min is not None
            and self.experience_max is not None
            and self.experience_min > self.experience_max
        ):
            raise ValidationError(
                {"experience_max": "experience_max must be greater than or equal to experience_min."}
            )


class VersionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING_APPROVAL = "pending_approval", "Pending Approval"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class JobDescriptionVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        JobRequisition,
        on_delete=models.CASCADE,
        related_name="description_versions",
    )
    version_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    overview = models.TextField(blank=True, default="")
    responsibilities = models.JSONField(default=list, blank=True)
    required_qualifications = models.JSONField(default=list, blank=True)
    preferred_qualifications = models.JSONField(default=list, blank=True)
    benefits = models.JSONField(default=list, blank=True)
    raw_content = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=VersionStatus.choices,
        default=VersionStatus.DRAFT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_jd_versions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "version_number"],
                name="unique_job_version_number",
            ),
        ]
        indexes = [
            models.Index(fields=["job", "status"], name="jd_version_job_status_idx"),
            models.Index(fields=["job", "-version_number"], name="jd_version_job_ver_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.job.title} - v{self.version_number} ({self.status})"

