from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai.providers.llm import get_llm_provider
from organizations.models import OrganizationMembership
from .filters import InterviewFilter
from .models import (
    Interview,
    InterviewFeedback,
    InterviewParticipant,
    InterviewStatus,
    InterviewTemplate,
    InterviewType,
)
from .permissions import (
    CAN_CONDUCT_INTERVIEWS,
    CAN_MANAGE_INTERVIEWS,
    get_interview_membership,
)
from .serializers import (
    InterviewCreateSerializer,
    InterviewDetailSerializer,
    InterviewFeedbackCreateSerializer,
    InterviewFeedbackSerializer,
    InterviewListSerializer,
    InterviewTemplateSerializer,
    InterviewUpdateSerializer,
)


class InterviewPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class InterviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing candidate interviews across the recruitment lifecycle.
    Multi-tenant scoped: users can only view or manage interviews in their active organisations.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = InterviewPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = InterviewFilter
    search_fields = [
        "title",
        "application__candidate__first_name",
        "application__candidate__last_name",
        "application__candidate__email",
        "application__job__title",
    ]
    ordering_fields = ["scheduled_start", "created_at", "status", "interview_type"]
    ordering = ["scheduled_start"]

    def _get_user_org_ids(self):
        return OrganizationMembership.objects.filter(
            user=self.request.user,
            is_active=True,
        ).values_list("organization_id", flat=True)

    def get_queryset(self):
        org_ids = self._get_user_org_ids()
        return (
            Interview.objects.filter(organization_id__in=org_ids)
            .select_related(
                "organization",
                "application",
                "application__candidate",
                "application__job",
                "application__resume",
                "template",
                "created_by",
            )
            .prefetch_related(
                "participants__user",
                "feedbacks__interviewer",
                "application__resume_analyses",
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return InterviewListSerializer
        if self.action == "retrieve":
            return InterviewDetailSerializer
        if self.action == "create":
            return InterviewCreateSerializer
        if self.action in ["update", "partial_update"]:
            return InterviewUpdateSerializer
        return InterviewDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = InterviewCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        interview = serializer.save()
        return Response(
            InterviewDetailSerializer(interview).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        interview = self.get_object()
        membership = get_interview_membership(request.user, interview.organization)
        if not membership or membership.role not in CAN_MANAGE_INTERVIEWS:
            return Response(
                {"detail": "You do not have permission to delete interviews in this organisation."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["get", "post"], url_path="feedback")
    def feedback(self, request, pk=None):
        """
        GET: Retrieve all submitted feedback for this interview.
        POST: Submit or update individual reviewer feedback.
        """
        interview = self.get_object()
        membership = get_interview_membership(request.user, interview.organization)

        if not membership or membership.role not in CAN_CONDUCT_INTERVIEWS:
            return Response(
                {"detail": "You do not have permission to access feedback for this interview."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.method == "GET":
            feedbacks = interview.feedbacks.select_related("interviewer").all()
            serializer = InterviewFeedbackSerializer(feedbacks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # POST: Submit / Update feedback
        # Verify user is either an assigned participant OR an admin/recruiter
        is_assigned = interview.participants.filter(user=request.user).exists()
        is_manager = membership.role in CAN_MANAGE_INTERVIEWS

        if not is_assigned and not is_manager:
            return Response(
                {"detail": "Only assigned interviewers or hiring managers can submit feedback."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = InterviewFeedbackCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        feedback_obj, created = InterviewFeedback.objects.update_or_create(
            interview=interview,
            interviewer=request.user,
            defaults={
                "rating": data["rating"],
                "recommendation": data.get("recommendation", "neutral"),
                "summary": data.get("summary", ""),
                "strengths": data.get("strengths", ""),
                "areas_for_improvement": data.get("areas_for_improvement", ""),
                "question_scores": data.get("question_scores", []),
            },
        )

        return Response(
            InterviewFeedbackSerializer(feedback_obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="generate-questions")
    def generate_questions(self, request, pk=None):
        """
        AI Interview Assistant: Suggests high-signal technical, behavioural, project,
        and competency questions tailored to this candidate and job requisition.
        """
        interview = self.get_object()
        app = interview.application
        job = app.job
        candidate = app.candidate

        # Extract structured candidate data
        parsed_resume = {}
        completed_analysis = app.resume_analyses.filter(status="completed").first()
        if completed_analysis and isinstance(completed_analysis.extracted_data, dict):
            parsed_resume = completed_analysis.extracted_data

        candidate_data = {
            "candidate_name": candidate.full_name,
            "summary": parsed_resume.get("summary", ""),
            "technical_skills": parsed_resume.get("technical_skills", []),
            "experience": parsed_resume.get("experience", []),
            "projects": parsed_resume.get("projects", []),
        }

        job_data = {
            "title": job.title,
            "department": job.department,
            "experience_min": job.experience_min,
            "experience_max": job.experience_max,
            "required_skills": job.required_skills,
            "responsibilities": job.responsibilities,
        }

        focus_areas = request.data.get("focus_areas", [])
        interview_type = request.data.get("interview_type", interview.interview_type)

        provider = get_llm_provider()
        questions_schema = provider.generate_interview_questions(
            job_data=job_data,
            candidate_data=candidate_data,
            interview_type=interview_type,
            focus_areas=focus_areas,
        )

        return Response(questions_schema.model_dump(), status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="calendar")
    def calendar(self, request):
        """
        Returns upcoming interviews optimized for calendar views.
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = InterviewListSerializer(queryset[:100], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InterviewTemplateViewSet(viewsets.ModelViewSet):
    """
    CRUD for organization interview guides and templates.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InterviewTemplateSerializer

    def _get_user_org_ids(self):
        return OrganizationMembership.objects.filter(
            user=self.request.user,
            is_active=True,
        ).values_list("organization_id", flat=True)

    def get_queryset(self):
        org_ids = self._get_user_org_ids()
        return InterviewTemplate.objects.filter(organization_id__in=org_ids)

    def perform_create(self, serializer):
        user = self.request.user
        org_id = self.request.data.get("organization_id")
        membership = OrganizationMembership.objects.filter(
            organization_id=org_id,
            user=user,
            is_active=True,
            role__in=CAN_MANAGE_INTERVIEWS,
        ).first()
        if not membership:
            raise PermissionError("You do not have permission to create interview templates in this organisation.")
        serializer.save(organization=membership.organization, created_by=user)
