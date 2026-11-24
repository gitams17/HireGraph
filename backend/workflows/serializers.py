from rest_framework import serializers
from workflows.models import WorkflowEvent, WorkflowExecution


class WorkflowEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowEvent
        fields = ["id", "event_type", "payload", "created_at"]


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    events = WorkflowEventSerializer(many=True, read_only=True)
    job_id = serializers.UUIDField(source="job.id", read_only=True)

    class Meta:
        model = WorkflowExecution
        fields = [
            "id",
            "thread_id",
            "job_id",
            "workflow_type",
            "status",
            "current_step",
            "error_message",
            "started_at",
            "completed_at",
            "events",
        ]
