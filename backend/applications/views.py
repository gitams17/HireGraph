from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.models import OrganizationMembership
from .filters import ApplicationFilter
from .models import Application, ApplicationEvent
from .permissions import CAN_MANAGE_APPLICATIONS, CAN_REVIEW_APPLICATIONS, get_application_membership
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationDetailSerializer,
    ApplicationListSerializer,
    ApplicationStageUpdateSerializer,
    RecruiterReviewSerializer,
    ResumeAnalysisSerializer,
)


class ApplicationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Candidate Applications to Job Requisitions.
    Multi-tenant scoped: callers only access applications in their active organisations.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = ApplicationPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ApplicationFilter
    search_fields = [
        "candidate__first_name",
        "candidate__last_name",
        "candidate__email",
        "job__title",
        "job__department",
    ]
    ordering_fields = ["created_at", "stage", "rating"]
    ordering = ["-created_at"]

    def _get_user_org_ids(self):
        return OrganizationMembership.objects.filter(
            user=self.request.user,
            is_active=True,
        ).values_list("organization_id", flat=True)

    def get_queryset(self):
        org_ids = self._get_user_org_ids()
        return (
            Application.objects.filter(organization_id__in=org_ids)
            .select_related("job", "candidate", "resume")
            .prefetch_related("events__actor")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ApplicationListSerializer
        if self.action == "retrieve":
            return ApplicationDetailSerializer
        if self.action == "create":
            return ApplicationCreateSerializer
        if self.action == "stage":
            return ApplicationStageUpdateSerializer
        return ApplicationDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = ApplicationCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        app = serializer.save()
        return Response(
            ApplicationDetailSerializer(app).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        app = self.get_object()
        membership = get_application_membership(request.user, app.organization)
        if not membership or membership.role not in CAN_MANAGE_APPLICATIONS:
            return Response(
                {"detail": "You do not have permission to delete applications in this organisation."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["patch"], url_path="stage")
    def stage(self, request, pk=None):
        """
        Transitions application stage and records audit history.
        """
        app = self.get_object()
        membership = get_application_membership(request.user, app.organization)
        if not membership or membership.role not in CAN_REVIEW_APPLICATIONS:
            return Response(
                {"detail": "You do not have permission to update application stages in this organisation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ApplicationStageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        from_stage = app.stage
        to_stage = data["stage"]

        app.stage = to_stage
        if "rating" in data and data["rating"] is not None:
            app.rating = data["rating"]
        if "rejection_reason" in data:
            app.rejection_reason = data["rejection_reason"]
        if "notes" in data and data["notes"]:
            app.notes = data["notes"]
        app.save()

        event_type = "stage_changed" if from_stage != to_stage else "updated"
        ApplicationEvent.objects.create(
            application=app,
            event_type=event_type,
            from_stage=from_stage,
            to_stage=to_stage,
            notes=data.get("notes", ""),
            actor=request.user,
        )

        return Response(ApplicationDetailSerializer(app).data)

    @action(detail=True, methods=["post"], url_path="analyze")
    def analyze(self, request, pk=None):
        """
        Triggers AI-powered resume screening using LangGraph and Celery.
        """
        app = self.get_object()
        membership = get_application_membership(request.user, app.organization)
        if not membership or membership.role not in CAN_REVIEW_APPLICATIONS:
            return Response(
                {"detail": "You do not have permission to analyze applications in this organisation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not app.resume:
            return Response(
                {"detail": "Cannot screen application: No resume is attached to this application."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.conf import settings
        from workflows.tasks import run_resume_screening_task

        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
            run_resume_screening_task(str(app.id), str(request.user.id))
        else:
            run_resume_screening_task.delay(str(app.id), str(request.user.id))

        latest = app.resume_analyses.first()
        if latest:
            return Response(ResumeAnalysisSerializer(latest).data, status=status.HTTP_200_OK)
        return Response(
            {"detail": "Resume screening initiated.", "status": "processing"},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"], url_path="analysis")
    def list_analyses(self, request, pk=None):
        """
        Retrieves all resume analyses performed for this application.
        """
        app = self.get_object()
        analyses = app.resume_analyses.all()
        return Response(ResumeAnalysisSerializer(analyses, many=True).data)

    @action(detail=True, methods=["get", "patch"], url_path=r"analysis/(?P<analysis_id>[^/.]+)")
    def retrieve_or_review_analysis(self, request, pk=None, analysis_id=None):
        """
        Retrieves or updates recruiter review on a specific ResumeAnalysis.
        """
        from django.shortcuts import get_object_or_404
        from .models import ResumeAnalysis

        app = self.get_object()
        analysis = get_object_or_404(ResumeAnalysis, id=analysis_id, application=app)

        if request.method == "GET":
            return Response(ResumeAnalysisSerializer(analysis).data)

        membership = get_application_membership(request.user, app.organization)
        if not membership or membership.role not in CAN_REVIEW_APPLICATIONS:
            return Response(
                {"detail": "You do not have permission to edit analysis reviews in this organisation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RecruiterReviewSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        if "extracted_data" in serializer.validated_data:
            analysis.extracted_data = serializer.validated_data["extracted_data"]
        if "recruiter_feedback" in serializer.validated_data:
            analysis.recruiter_feedback = serializer.validated_data["recruiter_feedback"]
        if "ats_score" in serializer.validated_data:
            analysis.ats_score = serializer.validated_data["ats_score"]
        analysis.save()

        ApplicationEvent.objects.create(
            application=app,
            event_type="recruiter_review_updated",
            notes="Recruiter modified AI screening extracted data / assessment.",
            actor=request.user,
        )

        return Response(ResumeAnalysisSerializer(analysis).data)

