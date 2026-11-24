import uuid
from django.db import models


class WorkflowStatus(models.TextChoices):
    RUNNING = "running", "Running"
    INTERRUPTED = "interrupted", "Interrupted (Awaiting Human Approval)"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class WorkflowExecution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread_id = models.CharField(max_length=255, unique=True, db_index=True)
    job = models.ForeignKey(
        "jobs.JobRequisition",
        on_delete=models.CASCADE,
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
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

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
