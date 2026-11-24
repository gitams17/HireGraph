from rest_framework import serializers

from organizations.models import Organization, OrganizationMembership
from .models import Candidate, Resume
from .permissions import CAN_MANAGE_CANDIDATES, get_candidate_membership
from .validators import validate_resume_file


class ResumeSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = [
            "id",
            "candidate_id",
            "file_name",
            "file_size",
            "content_type",
            "is_primary",
            "download_url",
            "uploaded_by_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_download_url(self, obj: Resume) -> str:
        return f"/api/v1/candidates/{obj.candidate_id}/resumes/{obj.id}/download/"

    def get_uploaded_by_name(self, obj: Resume) -> str | None:
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.email
        return None


class CandidateListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    resume_count = serializers.IntegerField(read_only=True, default=0)
    application_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Candidate
        fields = [
            "id",
            "organization",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "location",
            "current_company",
            "current_title",
            "total_experience_years",
            "skills",
            "resume_count",
            "application_count",
            "created_at",
            "updated_at",
        ]


class CandidateDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    resumes = ResumeSerializer(many=True, read_only=True)
    applications = serializers.SerializerMethodField()

    class Meta:
        model = Candidate
        fields = [
            "id",
            "organization",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "linkedin_url",
            "github_url",
            "portfolio_url",
            "location",
            "current_company",
            "current_title",
            "total_experience_years",
            "skills",
            "notes",
            "resumes",
            "applications",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_applications(self, obj: Candidate):
        # Return summary of applications
        return [
            {
                "id": str(app.id),
                "job_id": str(app.job_id),
                "job_title": app.job.title,
                "stage": app.stage,
                "created_at": app.created_at,
            }
            for app in obj.applications.select_related("job").all()
        ]


class CandidateWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            "organization",
            "first_name",
            "last_name",
            "email",
            "phone",
            "linkedin_url",
            "github_url",
            "portfolio_url",
            "location",
            "current_company",
            "current_title",
            "total_experience_years",
            "skills",
            "notes",
        ]

    def validate_email(self, value: str) -> str:
        return value.lower().strip()

    def validate(self, attrs):
        org = attrs.get("organization") or (self.instance.organization if self.instance else None)
        email = attrs.get("email") or (self.instance.email if self.instance else None)
        user = self.context["request"].user

        if org:
            membership = get_candidate_membership(user, org)
            if not membership or membership.role not in CAN_MANAGE_CANDIDATES:
                raise serializers.ValidationError(
                    {"organization": "You do not have permission to manage candidates in this organisation."}
                )

        if org and email:
            qs = Candidate.objects.filter(organization=org, email__iexact=email)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"email": "A candidate with this email address already exists in this organisation."}
                )

        return attrs


class ResumeUploadSerializer(serializers.Serializer):
    file = serializers.FileField(validators=[validate_resume_file])
    is_primary = serializers.BooleanField(default=True)
