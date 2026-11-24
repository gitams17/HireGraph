import uuid
from django.conf import settings
from django.db import models


class WorkflowStatus(models.TextChoices):
    RUNNING = "running", "Running"
    INTERRUPTED = "interrupted", "Interrupted (Awaiting Human Approval)"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class WorkflowExecution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread_id = models.CharField(max_length=255, unique=True, db_index=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="workflow_executions",
    )
    job = models.ForeignKey(
        "jobs.JobRequisition",
        on_delete=models.CASCADE,
        related_name="workflow_executions",
    )
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflow_executions",
    )
    workflow_type = models.CharField(max_length=50, default="job_description")
    status = models.CharField(
        max_length=50,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.RUNNING,
    )
    current_step = models.CharField(max_length=100, default="")
    error_message = models.TextField(blank=True, default="")
    state_snapshot = models.JSONField(default=dict, blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    last_retried_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["workflow_type"]),
            models.Index(fields=["organization", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.workflow_type} [{self.thread_id}] - {self.status}"


class WorkflowEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(
        WorkflowExecution,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=50)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.execution.thread_id} - {self.event_type} at {self.created_at}"


# ---------------------------------------------------------------------------
# Phase 8: Job Board Publications
# ---------------------------------------------------------------------------

class JobPublicationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PUBLISHED = "published", "Published"
    FAILED = "failed", "Failed"
    EXPIRED = "expired", "Expired"


class JobPublication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(
        "jobs.JobRequisition",
        on_delete=models.CASCADE,
        related_name="publications",
    )
    board_name = models.CharField(max_length=50)  # linkedin, indeed, mock_board
    external_id = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=JobPublicationStatus.choices,
        default=JobPublicationStatus.PENDING,
    )
    posting_url = models.CharField(max_length=500, blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "board_name"],
                name="unique_job_board_publication",
            )
        ]

    def __str__(self) -> str:
        return f"{self.job.title} on {self.board_name} [{self.status}]"


# ---------------------------------------------------------------------------
# Phase 8: Offer Management & Negotiation
# ---------------------------------------------------------------------------

class OfferStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING_APPROVAL = "pending_approval", "Pending Approval"
    APPROVED = "approved", "Approved"
    SENT = "sent", "Sent to Candidate"
    NEGOTIATING = "negotiating", "Negotiating"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"


class Offer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="offers",
    )
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="offers",
    )
    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    equity = models.CharField(max_length=100, blank=True, default="")
    sign_on_bonus = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    status = models.CharField(
        max_length=30,
        choices=OfferStatus.choices,
        default=OfferStatus.DRAFT,
    )
    candidate_response = models.CharField(max_length=50, blank=True, default="")
    negotiation_notes = models.TextField(blank=True, default="")
    counter_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    terms = models.TextField(blank=True, default="")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_offers",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_offers",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["application", "status"]),
        ]

    def __str__(self) -> str:
        return f"Offer for {self.application.candidate.full_name}: {self.currency} {self.base_salary} [{self.status}]"


# ---------------------------------------------------------------------------
# Phase 8: Candidate Onboarding
# ---------------------------------------------------------------------------

class OnboardingTaskCategory(models.TextChoices):
    COMPLIANCE = "compliance", "Compliance & Legal"
    IT_SETUP = "it_setup", "IT & Hardware Setup"
    HR_PAPERWORK = "hr_paperwork", "HR Paperwork"
    TEAM_INTRO = "team_intro", "Team & Orientation"


class OnboardingTaskStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    SKIPPED = "skipped", "Skipped"


class OnboardingTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="onboarding_tasks",
    )
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="onboarding_tasks",
    )
    title = models.CharField(max_length=255)
    category = models.CharField(
        max_length=30,
        choices=OnboardingTaskCategory.choices,
        default=OnboardingTaskCategory.COMPLIANCE,
    )
    status = models.CharField(
        max_length=20,
        choices=OnboardingTaskStatus.choices,
        default=OnboardingTaskStatus.PENDING,
    )
    due_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_onboarding_tasks",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["application", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.status}) for {self.application.candidate.full_name}"
