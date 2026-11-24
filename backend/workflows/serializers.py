from rest_framework import serializers

from applications.models import Application
from jobs.models import JobRequisition
from workflows.models import (
    JobPublication,
    Offer,
    OfferStatus,
    OnboardingTask,
    WorkflowEvent,
    WorkflowExecution,
)


class WorkflowEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowEvent
        fields = ["id", "event_type", "payload", "created_at"]


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    events = WorkflowEventSerializer(many=True, read_only=True)
    job_id = serializers.UUIDField(source="job.id", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    candidate_name = serializers.CharField(
        source="application.candidate.full_name", default=None, read_only=True
    )

    class Meta:
        model = WorkflowExecution
        fields = [
            "id",
            "thread_id",
            "organization",
            "job_id",
            "job_title",
            "application",
            "candidate_name",
            "workflow_type",
            "status",
            "current_step",
            "error_message",
            "state_snapshot",
            "retry_count",
            "last_retried_at",
            "started_at",
            "completed_at",
            "events",
        ]


class StartRecruitmentWorkflowSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    minimum_applicants = serializers.IntegerField(default=1, min_value=1)

    def validate_job_id(self, value):
        if not JobRequisition.objects.filter(id=value).exists():
            raise serializers.ValidationError("JobRequisition with this ID does not exist.")
        return value


class ResumeWorkflowSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=["approved", "rejected", "negotiate"], default="approved")
    feedback = serializers.CharField(required=False, allow_blank=True, default="")
    base_salary = serializers.FloatField(required=False, allow_null=True)
    revised_terms = serializers.DictField(required=False, default=dict)


class JobPublicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job.title", read_only=True)

    class Meta:
        model = JobPublication
        fields = [
            "id",
            "job",
            "job_title",
            "board_name",
            "external_id",
            "status",
            "posting_url",
            "payload",
            "published_at",
            "created_at",
        ]


class OfferSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="application.candidate.full_name", read_only=True)
    candidate_email = serializers.CharField(source="application.candidate.email", read_only=True)
    job_title = serializers.CharField(source="application.job.title", read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "organization",
            "application",
            "candidate_name",
            "candidate_email",
            "job_title",
            "base_salary",
            "currency",
            "equity",
            "sign_on_bonus",
            "start_date",
            "status",
            "candidate_response",
            "negotiation_notes",
            "counter_salary",
            "terms",
            "approved_by",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class OfferResponseSerializer(serializers.Serializer):
    response = serializers.ChoiceField(choices=["accepted", "negotiation", "rejected"])
    counter_salary = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    negotiation_notes = serializers.CharField(required=False, allow_blank=True, default="")


class OnboardingTaskSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="application.candidate.full_name", read_only=True)

    class Meta:
        model = OnboardingTask
        fields = [
            "id",
            "organization",
            "application",
            "candidate_name",
            "title",
            "category",
            "status",
            "due_date",
            "assigned_to",
            "completed_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
