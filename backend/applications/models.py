import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class ApplicationStage(models.TextChoices):
    APPLIED = "applied", "Applied"
    UNDER_REVIEW = "under_review", "Under Review"
    SHORTLISTED = "shortlisted", "Shortlisted"
    INTERVIEW = "interview", "Interview"
    SELECTED = "selected", "Selected"
    REJECTED = "rejected", "Rejected"


class Application(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    job = models.ForeignKey(
        "jobs.JobRequisition",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    candidate = models.ForeignKey(
        "candidates.Candidate",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    resume = models.ForeignKey(
        "candidates.Resume",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    stage = models.CharField(
        max_length=30,
        choices=ApplicationStage.choices,
        default=ApplicationStage.APPLIED,
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    rejection_reason = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_applications",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "candidate"],
                name="unique_candidate_application_per_job",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "stage"]),
            models.Index(fields=["job", "stage"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.candidate.full_name} -> {self.job.title} [{self.stage}]"


class ApplicationEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=50)  # e.g., "created", "stage_changed", "note_added"
    from_stage = models.CharField(max_length=30, blank=True, default="")
    to_stage = models.CharField(max_length=30, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Event [{self.event_type}]: {self.from_stage} -> {self.to_stage} on {self.application_id}"


class AnalysisStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class ResumeAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="resume_analyses",
    )
    resume = models.ForeignKey(
        "candidates.Resume",
        on_delete=models.CASCADE,
        related_name="analyses",
    )
    model_name = models.CharField(max_length=100, default="fake")
    prompt_version = models.CharField(max_length=50, default="v1.0")
    evaluation_rubric_version = models.CharField(max_length=50, default="v1.0")

    extracted_data = models.JSONField(default=dict, blank=True)
    assessment = models.JSONField(default=dict, blank=True)
    ats_score = models.PositiveSmallIntegerField(null=True, blank=True)
    recruiter_feedback = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=20,
        choices=AnalysisStatus.choices,
        default=AnalysisStatus.PENDING,
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["application", "-created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Analysis [{self.status}] score={self.ats_score} for App {self.application_id}"

