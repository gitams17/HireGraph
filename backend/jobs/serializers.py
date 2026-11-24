from rest_framework import serializers

from accounts.serializers import UserSerializer
from .models import JobRequisition


class JobRequisitionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list endpoints."""

    created_by = UserSerializer(read_only=True)

    class Meta:
        model = JobRequisition
        fields = [
            "id",
            "title",
            "department",
            "location",
            "employment_type",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        ]


class JobRequisitionDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail/create/update responses."""

    created_by = UserSerializer(read_only=True)
    organization = serializers.UUIDField(source="organization.id", read_only=True)

    class Meta:
        model = JobRequisition
        fields = [
            "id",
            "organization",
            "title",
            "department",
            "location",
            "employment_type",
            "experience_min",
            "experience_max",
            "required_skills",
            "responsibilities",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        ]


class JobRequisitionWriteSerializer(serializers.ModelSerializer):
    """Serializer for create/update operations (write path)."""

    class Meta:
        model = JobRequisition
        fields = [
            "title",
            "department",
            "location",
            "employment_type",
            "experience_min",
            "experience_max",
            "required_skills",
            "responsibilities",
            "status",
        ]

    def validate_required_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("required_skills must be a list of strings.")
        if not all(isinstance(item, str) for item in value):
            raise serializers.ValidationError("Each skill must be a string.")
        return value

    def validate_responsibilities(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("responsibilities must be a list of strings.")
        if not all(isinstance(item, str) for item in value):
            raise serializers.ValidationError("Each responsibility must be a string.")
        return value

    def validate(self, attrs):
        exp_min = attrs.get("experience_min")
        exp_max = attrs.get("experience_max")

        # For partial updates, fall back to instance values
        if self.instance:
            exp_min = exp_min if "experience_min" in attrs else self.instance.experience_min
            exp_max = exp_max if "experience_max" in attrs else self.instance.experience_max

        if exp_min is not None and exp_max is not None and exp_min > exp_max:
            raise serializers.ValidationError(
                {"experience_max": "experience_max must be >= experience_min."}
            )
        return attrs
