from pathlib import Path
import re
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

private_resume_storage = FileSystemStorage(
    location=str(settings.PRIVATE_MEDIA_ROOT),
    base_url=None,  # No public URL
)


def candidate_resume_upload_path(instance, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", Path(filename).stem)[:60]
    unique_suffix = uuid.uuid4().hex[:10]
    return f"resumes/{instance.candidate.organization_id}/{instance.candidate.id}/{unique_suffix}_{clean_stem}{ext}"


class Candidate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="candidates",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True, default="")
    linkedin_url = models.URLField(blank=True, default="")
    github_url = models.URLField(blank=True, default="")
    portfolio_url = models.URLField(blank=True, default="")
    location = models.CharField(max_length=150, blank=True, default="")
    current_company = models.CharField(max_length=150, blank=True, default="")
    current_title = models.CharField(max_length=150, blank=True, default="")
    total_experience_years = models.PositiveIntegerField(null=True, blank=True)
    skills = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_candidates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "email"],
                name="unique_candidate_email_per_org",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "-created_at"]),
            models.Index(fields=["organization", "email"]),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    file = models.FileField(
        storage=private_resume_storage,
        upload_to=candidate_resume_upload_path,
    )
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # Bytes
    content_type = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_resumes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Resume: {self.file_name} for {self.candidate.full_name}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Set other resumes for this candidate to non-primary
            Resume.objects.filter(candidate=self.candidate, is_primary=True).exclude(
                pk=self.pk
            ).update(is_primary=False)
        super().save(*args, **kwargs)
