from rest_framework import serializers

from candidates.models import Candidate, Resume
from candidates.serializers import ResumeSerializer
from jobs.models import JobRequisition
from .models import Application, ApplicationEvent, ApplicationStage, ResumeAnalysis
from .permissions import CAN_MANAGE_APPLICATIONS, get_application_membership


class ApplicationEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationEvent
        fields = [
            "id",
            "application_id",
            "event_type",
            "from_stage",
            "to_stage",
            "notes",
            "actor_name",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj: ApplicationEvent) -> str | None:
        if obj.actor:
            return f"{obj.actor.first_name} {obj.actor.last_name}".strip() or obj.actor.email
        return None


class ApplicationListSerializer(serializers.ModelSerializer):
    candidate_id = serializers.UUIDField(source="candidate.id", read_only=True)
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    candidate_email = serializers.EmailField(source="candidate.email", read_only=True)
    candidate_company = serializers.CharField(source="candidate.current_company", read_only=True)
    candidate_title = serializers.CharField(source="candidate.current_title", read_only=True)

    job_id = serializers.UUIDField(source="job.id", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    job_department = serializers.CharField(source="job.department", read_only=True)

    has_resume = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "organization_id",
            "job_id",
            "job_title",
            "job_department",
            "candidate_id",
            "candidate_name",
            "candidate_email",
            "candidate_company",
            "candidate_title",
            "stage",
            "rating",
            "has_resume",
            "created_at",
            "updated_at",
        ]

    def get_has_resume(self, obj: Application) -> bool:
        return obj.resume_id is not None


class ApplicationDetailSerializer(serializers.ModelSerializer):
    candidate = serializers.SerializerMethodField()
    job = serializers.SerializerMethodField()
    resume = ResumeSerializer(read_only=True)
    events = ApplicationEventSerializer(many=True, read_only=True)
    latest_analysis = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "organization_id",
            "job",
            "candidate",
            "resume",
            "stage",
            "rating",
            "rejection_reason",
            "notes",
            "latest_analysis",
            "events",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_latest_analysis(self, obj: Application):
        analysis = obj.resume_analyses.first()
        if analysis:
            return ResumeAnalysisSerializer(analysis).data
        return None

    def get_candidate(self, obj: Application):
        return {
            "id": str(obj.candidate.id),
            "full_name": obj.candidate.full_name,
            "first_name": obj.candidate.first_name,
            "last_name": obj.candidate.last_name,
            "email": obj.candidate.email,
            "phone": obj.candidate.phone,
            "current_company": obj.candidate.current_company,
            "current_title": obj.candidate.current_title,
            "location": obj.candidate.location,
            "skills": obj.candidate.skills,
        }

    def get_job(self, obj: Application):
        return {
            "id": str(obj.job.id),
            "title": obj.job.title,
            "department": obj.job.department,
            "location": obj.job.location,
            "status": obj.job.status,
        }


class ApplicationCreateSerializer(serializers.Serializer):
    job_id = serializers.UUIDField()
    candidate_id = serializers.UUIDField()
    resume_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        user = self.context["request"].user
        job_id = attrs["job_id"]
        candidate_id = attrs["candidate_id"]
        resume_id = attrs.get("resume_id")

        try:
            job = JobRequisition.objects.get(id=job_id)
        except JobRequisition.DoesNotExist:
            raise serializers.ValidationError({"job_id": "Job requisition not found."})

        # Check caller has permission on this job's organisation
        membership = get_application_membership(user, job.organization)
        if not membership or membership.role not in CAN_MANAGE_APPLICATIONS:
            raise serializers.ValidationError(
                {"job_id": "You do not have permission to create applications for this organisation."}
            )

        try:
            candidate = Candidate.objects.get(id=candidate_id)
        except Candidate.DoesNotExist:
            raise serializers.ValidationError({"candidate_id": "Candidate not found."})

        if candidate.organization_id != job.organization_id:
            raise serializers.ValidationError(
                {"candidate_id": "Candidate does not belong to the same organisation as the job requisition."}
            )

        # Duplicate prevention check
        if Application.objects.filter(job=job, candidate=candidate).exists():
            raise serializers.ValidationError(
                {"non_field_errors": ["This candidate has already applied to this job requisition."]}
            )

        # Resume verification
        resume = None
        if resume_id:
            try:
                resume = Resume.objects.get(id=resume_id, candidate=candidate)
            except Resume.DoesNotExist:
                raise serializers.ValidationError({"resume_id": "Specified resume not found for this candidate."})
        else:
            # Pick candidate's primary resume if available
            resume = candidate.resumes.filter(is_primary=True).first() or candidate.resumes.first()

        attrs["job"] = job
        attrs["candidate"] = candidate
        attrs["resume"] = resume
        attrs["organization"] = job.organization
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        app = Application.objects.create(
            organization=validated_data["organization"],
            job=validated_data["job"],
            candidate=validated_data["candidate"],
            resume=validated_data.get("resume"),
            notes=validated_data.get("notes", ""),
            stage=ApplicationStage.APPLIED,
            created_by=user,
        )

        ApplicationEvent.objects.create(
            application=app,
            event_type="created",
            to_stage=ApplicationStage.APPLIED,
            notes="Application submitted/created.",
            actor=user,
        )
        return app


class ApplicationStageUpdateSerializer(serializers.Serializer):
    stage = serializers.ChoiceField(choices=ApplicationStage.choices)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    rejection_reason = serializers.CharField(required=False, allow_blank=True, default="")
    rating = serializers.IntegerField(required=False, min_value=1, max_value=5, allow_null=True)


class ResumeAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeAnalysis
        fields = [
            "id",
            "application_id",
            "resume_id",
            "model_name",
            "prompt_version",
            "evaluation_rubric_version",
            "extracted_data",
            "assessment",
            "ats_score",
            "recruiter_feedback",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "application_id",
            "resume_id",
            "model_name",
            "prompt_version",
            "evaluation_rubric_version",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]


class RecruiterReviewSerializer(serializers.Serializer):
    extracted_data = serializers.JSONField(required=False)
    recruiter_feedback = serializers.JSONField(required=False)
    ats_score = serializers.IntegerField(required=False, min_value=0, max_value=100)

