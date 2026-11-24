from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from applications.models import Application, ApplicationEvent, ApplicationStage
from organizations.models import OrganizationMembership
from .models import (
    Interview,
    InterviewFeedback,
    InterviewNotification,
    InterviewParticipant,
    InterviewStatus,
    InterviewTemplate,
    InterviewType,
    ParticipantRole,
    ParticipantStatus,
    Recommendation,
)
from .permissions import CAN_MANAGE_INTERVIEWS, get_interview_membership

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name"]


class InterviewParticipantSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = InterviewParticipant
        fields = ["id", "user", "user_id", "role", "status", "created_at"]


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    interviewer = UserBriefSerializer(read_only=True)

    class Meta:
        model = InterviewFeedback
        fields = [
            "id",
            "interview",
            "interviewer",
            "rating",
            "recommendation",
            "summary",
            "strengths",
            "areas_for_improvement",
            "question_scores",
            "submitted_at",
            "updated_at",
        ]
        read_only_fields = ["id", "interview", "interviewer", "submitted_at", "updated_at"]


class InterviewFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewFeedback
        fields = [
            "rating",
            "recommendation",
            "summary",
            "strengths",
            "areas_for_improvement",
            "question_scores",
        ]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class InterviewTemplateSerializer(serializers.ModelSerializer):
    created_by = UserBriefSerializer(read_only=True)

    class Meta:
        model = InterviewTemplate
        fields = [
            "id",
            "organization",
            "name",
            "interview_type",
            "description",
            "default_duration_minutes",
            "default_questions",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class InterviewListSerializer(serializers.ModelSerializer):
    candidate_id = serializers.UUIDField(source="application.candidate.id", read_only=True)
    candidate_name = serializers.CharField(source="application.candidate.full_name", read_only=True)
    candidate_email = serializers.CharField(source="application.candidate.email", read_only=True)
    job_id = serializers.UUIDField(source="application.job.id", read_only=True)
    job_title = serializers.CharField(source="application.job.title", read_only=True)
    participants = InterviewParticipantSerializer(many=True, read_only=True)
    feedbacks_count = serializers.IntegerField(source="feedbacks.count", read_only=True)

    class Meta:
        model = Interview
        fields = [
            "id",
            "organization",
            "application_id",
            "candidate_id",
            "candidate_name",
            "candidate_email",
            "job_id",
            "job_title",
            "template",
            "title",
            "interview_type",
            "status",
            "scheduled_start",
            "scheduled_end",
            "location_type",
            "meeting_link",
            "location_details",
            "participants",
            "feedbacks_count",
            "created_at",
            "updated_at",
        ]


class InterviewDetailSerializer(serializers.ModelSerializer):
    application = serializers.SerializerMethodField()
    participants = InterviewParticipantSerializer(many=True, read_only=True)
    feedbacks = InterviewFeedbackSerializer(many=True, read_only=True)
    created_by = UserBriefSerializer(read_only=True)

    class Meta:
        model = Interview
        fields = [
            "id",
            "organization",
            "application",
            "template",
            "title",
            "interview_type",
            "status",
            "scheduled_start",
            "scheduled_end",
            "location_type",
            "meeting_link",
            "location_details",
            "prepared_questions",
            "notes",
            "participants",
            "feedbacks",
            "created_by",
            "created_at",
            "updated_at",
        ]

    def get_application(self, obj):
        app = obj.application
        candidate = app.candidate
        job = app.job
        resume = app.resume

        # Include latest analysis score if available
        latest_analysis = getattr(app, "resume_analyses", None)
        analysis_data = None
        if latest_analysis and latest_analysis.filter(status="completed").exists():
            first_analysis = latest_analysis.filter(status="completed").first()
            analysis_data = {
                "id": str(first_analysis.id),
                "ats_score": first_analysis.ats_score,
                "summary_headline": first_analysis.assessment.get("summary_headline", "") if isinstance(first_analysis.assessment, dict) else "",
            }

        return {
            "id": str(app.id),
            "stage": app.stage,
            "candidate": {
                "id": str(candidate.id),
                "full_name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "linkedin_url": candidate.linkedin_url,
                "github_url": candidate.github_url,
            },
            "job": {
                "id": str(job.id),
                "title": job.title,
                "department": job.department,
                "required_skills": job.required_skills,
                "responsibilities": job.responsibilities,
            },
            "resume": {
                "id": str(resume.id) if resume else None,
                "file_name": resume.file_name if resume else None,
            } if resume else None,
            "latest_analysis": analysis_data,
        }


class InterviewCreateSerializer(serializers.ModelSerializer):
    application_id = serializers.UUIDField(write_only=True)
    interviewer_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
        write_only=True,
    )
    template_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Interview
        fields = [
            "id",
            "application_id",
            "template_id",
            "title",
            "interview_type",
            "scheduled_start",
            "scheduled_end",
            "location_type",
            "meeting_link",
            "location_details",
            "prepared_questions",
            "notes",
            "interviewer_ids",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        start = attrs.get("scheduled_start")
        end = attrs.get("scheduled_end")
        if start and end and end <= start:
            raise serializers.ValidationError({"scheduled_end": "Scheduled end time must be after start time."})

        # Validate application
        app_id = attrs.get("application_id")
        user = self.context["request"].user
        try:
            application = Application.objects.select_related("organization", "job", "candidate").get(id=app_id)
        except Application.DoesNotExist:
            raise serializers.ValidationError({"application_id": "Application does not exist."})

        # Validate permission in application's org
        membership = get_interview_membership(user, application.organization)
        if not membership or membership.role not in CAN_MANAGE_INTERVIEWS:
            raise serializers.ValidationError(
                {"detail": "You do not have permission to schedule interviews in this organisation."}
            )

        # Validate interviewers belong to org
        interviewer_ids = attrs.get("interviewer_ids", [])
        if interviewer_ids:
            valid_users = OrganizationMembership.objects.filter(
                organization=application.organization,
                user_id__in=interviewer_ids,
                is_active=True,
            ).values_list("user_id", flat=True)
            invalid_ids = set(interviewer_ids) - set(valid_users)
            if invalid_ids:
                raise serializers.ValidationError(
                    {"interviewer_ids": f"User(s) {list(invalid_ids)} are not active members of this organisation."}
                )

        attrs["_application"] = application
        attrs["_organization"] = application.organization
        return attrs

    def create(self, validated_data):
        application = validated_data.pop("_application")
        organization = validated_data.pop("_organization")
        interviewer_ids = validated_data.pop("interviewer_ids", [])
        validated_data.pop("application_id", None)
        template_id = validated_data.pop("template_id", None)
        user = self.context["request"].user

        template = None
        if template_id:
            template = InterviewTemplate.objects.filter(id=template_id, organization=organization).first()

        interview = Interview.objects.create(
            organization=organization,
            application=application,
            template=template,
            created_by=user,
            **validated_data,
        )

        # Create participants
        for uid in interviewer_ids:
            InterviewParticipant.objects.create(
                interview=interview,
                user_id=uid,
                role=ParticipantRole.INTERVIEWER,
                status=ParticipantStatus.INVITED,
            )
            # Create in-app notification
            InterviewNotification.objects.create(
                interview=interview,
                recipient_id=uid,
                notification_type="interview_scheduled",
                title=f"New Interview Scheduled: {interview.title}",
                message=f"You have been assigned as an interviewer for {application.candidate.full_name} for the role of {application.job.title}.",
            )

        # Auto-transition application stage to 'interview' if currently prior stage
        if application.stage in [ApplicationStage.APPLIED, ApplicationStage.UNDER_REVIEW, ApplicationStage.SHORTLISTED]:
            old_stage = application.stage
            application.stage = ApplicationStage.INTERVIEW
            application.save(update_fields=["stage", "updated_at"])
            ApplicationEvent.objects.create(
                application=application,
                event_type="stage_changed",
                from_stage=old_stage,
                to_stage=ApplicationStage.INTERVIEW,
                notes=f"Application moved to Interview upon scheduling: {interview.title}",
                actor=user,
            )

        return interview


class InterviewUpdateSerializer(serializers.ModelSerializer):
    interviewer_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Interview
        fields = [
            "title",
            "interview_type",
            "status",
            "scheduled_start",
            "scheduled_end",
            "location_type",
            "meeting_link",
            "location_details",
            "prepared_questions",
            "notes",
            "interviewer_ids",
        ]

    def validate(self, attrs):
        start = attrs.get("scheduled_start") or getattr(self.instance, "scheduled_start", None)
        end = attrs.get("scheduled_end") or getattr(self.instance, "scheduled_end", None)
        if start and end and end <= start:
            raise serializers.ValidationError({"scheduled_end": "Scheduled end time must be after start time."})
        return attrs

    def update(self, instance, validated_data):
        interviewer_ids = validated_data.pop("interviewer_ids", None)
        old_status = instance.status

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If interviewer_ids was provided, sync participants
        if interviewer_ids is not None:
            existing_participants = set(instance.participants.values_list("user_id", flat=True))
            new_ids = set(interviewer_ids)

            # Remove unselected participants
            instance.participants.filter(user_id__in=(existing_participants - new_ids)).delete()

            # Add newly selected participants
            for uid in (new_ids - existing_participants):
                InterviewParticipant.objects.create(
                    interview=instance,
                    user_id=uid,
                    role=ParticipantRole.INTERVIEWER,
                    status=ParticipantStatus.INVITED,
                )
                InterviewNotification.objects.create(
                    interview=instance,
                    recipient_id=uid,
                    notification_type="interview_updated",
                    title=f"Interview Assignment: {instance.title}",
                    message=f"You have been assigned to interview {instance.application.candidate.full_name}.",
                )

        # Notify participants if status changed
        if "status" in validated_data and validated_data["status"] != old_status:
            for p in instance.participants.select_related("user"):
                InterviewNotification.objects.create(
                    interview=instance,
                    recipient=p.user,
                    notification_type="interview_updated",
                    title=f"Interview Status Updated: {instance.title}",
                    message=f"Interview status has been updated to {instance.status}.",
                )

        return instance
