import uuid
from django.conf import settings
from django.db import models


class ApprovalStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class ApprovalRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="approval_requests",
    )
    job = models.ForeignKey(
        "jobs.JobRequisition",
        on_delete=models.CASCADE,
        related_name="approval_requests",
    )
    version = models.ForeignKey(
        "jobs.JobDescriptionVersion",
        on_delete=models.CASCADE,
        related_name="approval_requests",
    )
    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_approvals",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_approvals",
    )
    feedback = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status"], name="approval_org_status_idx"),
            models.Index(fields=["job", "status"], name="approval_job_status_idx"),
        ]

    def __str__(self) -> str:
        return f"Approval for {self.job.title} v{self.version.version_number} ({self.status})"
