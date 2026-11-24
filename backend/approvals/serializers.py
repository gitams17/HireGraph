from rest_framework import serializers
from accounts.serializers import UserSerializer
from approvals.models import ApprovalRequest


class ApprovalRequestSerializer(serializers.ModelSerializer):
    requested_by = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    job_id = serializers.UUIDField(source="job.id", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    version_number = serializers.IntegerField(source="version.version_number", read_only=True)
    version_id = serializers.UUIDField(source="version.id", read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = [
            "id",
            "organization",
            "job_id",
            "job_title",
            "version_id",
            "version_number",
            "status",
            "requested_by",
            "reviewed_by",
            "feedback",
            "created_at",
            "decided_at",
        ]


class DecisionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])
    feedback = serializers.CharField(required=False, allow_blank=True, default="")
