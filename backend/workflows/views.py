from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from jobs.models import JobRequisition
from organizations.models import OrganizationMembership
from workflows.models import (
    JobPublication,
    Offer,
    OfferStatus,
    OnboardingTask,
    OnboardingTaskStatus,
    WorkflowEvent,
    WorkflowExecution,
    WorkflowStatus,
)
from workflows.serializers import (
    JobPublicationSerializer,
    OfferResponseSerializer,
    OfferSerializer,
    OnboardingTaskSerializer,
    ResumeWorkflowSerializer,
    StartRecruitmentWorkflowSerializer,
    WorkflowExecutionSerializer,
)
from workflows.services import WorkflowOrchestrationService


class WorkflowPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class WorkflowViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing, initiating, resuming, and retrying recruitment workflows.
    Multi-tenant scoped to user's active organisations.
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = WorkflowPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "workflow_type", "job"]
    search_fields = [
        "thread_id",
        "job__title",
        "job__department",
        "application__candidate__first_name",
        "application__candidate__last_name",
    ]
    ordering_fields = ["started_at", "completed_at", "status"]
    ordering = ["-started_at"]

    def _get_user_org_ids(self):
        return OrganizationMembership.objects.filter(
            user=self.request.user,
            is_active=True,
        ).values_list("organization_id", flat=True)

    def get_queryset(self):
        org_ids = self._get_user_org_ids()
        return (
            WorkflowExecution.objects.filter(
                Q(organization_id__in=org_ids) | Q(job__organization_id__in=org_ids)
            )
            .select_related("job", "organization", "application", "application__candidate")
            .prefetch_related("events")
            .distinct()
        )

    def get_serializer_class(self):
        return WorkflowExecutionSerializer

    @action(detail=False, methods=["post"], url_path="recruitment/start")
    def start_recruitment(self, request):
        """Initiate the Master Recruitment Workflow (Phase 8) for a Job Requisition."""
        serializer = StartRecruitmentWorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job_id = serializer.validated_data["job_id"]
        minimum_applicants = serializer.validated_data.get("minimum_applicants", 1)

        job = get_object_or_404(JobRequisition, id=job_id)

        # Enforce org membership
        is_member = OrganizationMembership.objects.filter(
            organization=job.organization,
            user=request.user,
            is_active=True,
        ).exists()
        if not is_member:
            return Response(
                {"detail": "You do not have permission in this organisation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        execution = WorkflowOrchestrationService.start_recruitment_workflow(
            job=job,
            user=request.user,
            minimum_applicants=minimum_applicants,
        )

        return Response(
            WorkflowExecutionSerializer(execution).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="resume")
    def resume_execution(self, request, pk=None):
        """Resume an interrupted workflow execution at a human decision gate."""
        execution = self.get_object()
        serializer = ResumeWorkflowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resume_data = serializer.validated_data

        if execution.workflow_type == "recruitment":
            updated_execution = WorkflowOrchestrationService.resume_recruitment_workflow(
                execution=execution,
                resume_data=resume_data,
                user=request.user,
            )
        else:
            updated_execution = WorkflowOrchestrationService.resume_job_description_workflow(
                thread_id=execution.thread_id,
                decision=resume_data.get("decision", "approved"),
                feedback=resume_data.get("feedback", ""),
                user=request.user,
            )

        return Response(
            WorkflowExecutionSerializer(updated_execution or execution).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="retry")
    def retry_execution(self, request, pk=None):
        """Manually retry a failed workflow execution from its last checkpoint."""
        execution = self.get_object()
        if execution.status != WorkflowStatus.FAILED:
            return Response(
                {"detail": "Only failed workflow executions can be retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        retried_execution = WorkflowOrchestrationService.retry_workflow_execution(execution)
        return Response(
            WorkflowExecutionSerializer(retried_execution).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard_metrics(self, request):
        """Summary metrics for the workflow automation dashboard."""
        qs = self.get_queryset()
        total = qs.count()
        active = qs.filter(status=WorkflowStatus.RUNNING).count()
        pending_approvals = qs.filter(status=WorkflowStatus.INTERRUPTED).count()
        failed = qs.filter(status=WorkflowStatus.FAILED).count()
        completed = qs.filter(status=WorkflowStatus.COMPLETED).count()

        recent_events = (
            WorkflowEvent.objects.filter(execution__in=qs[:50])
            .select_related("execution", "execution__job")
            .order_by("-created_at")[:10]
        )

        return Response(
            {
                "total_executions": total,
                "active_count": active,
                "pending_approvals_count": pending_approvals,
                "failed_count": failed,
                "completed_count": completed,
                "recent_events": [
                    {
                        "id": str(e.id),
                        "thread_id": e.execution.thread_id,
                        "job_title": e.execution.job.title,
                        "event_type": e.event_type,
                        "payload": e.payload,
                        "created_at": e.created_at.isoformat(),
                    }
                    for e in recent_events
                ],
            },
            status=status.HTTP_200_OK,
        )


class OfferViewSet(viewsets.ModelViewSet):
    """ViewSet for managing job offers and candidate negotiation rounds."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OfferSerializer

    def _get_user_org_ids(self):
        return OrganizationMembership.objects.filter(
            user=self.request.user,
            is_active=True,
        ).values_list("organization_id", flat=True)

    def get_queryset(self):
        org_ids = self._get_user_org_ids()
        return (
            Offer.objects.filter(organization_id__in=org_ids)
            .select_related("organization", "application", "application__candidate", "application__job")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="respond")
    def record_response(self, request, pk=None):
        """Record candidate response (accepted, negotiation, rejected) and resume workflow."""
        offer = self.get_object()
        serializer = OfferResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resp = serializer.validated_data["response"]
        counter_salary = serializer.validated_data.get("counter_salary")
        notes = serializer.validated_data.get("negotiation_notes", "")

        offer.candidate_response = resp
        if resp == "accepted":
            offer.status = OfferStatus.ACCEPTED
        elif resp == "negotiation":
            offer.status = OfferStatus.NEGOTIATING
            offer.counter_salary = counter_salary
            offer.negotiation_notes = notes
        elif resp == "rejected":
            offer.status = OfferStatus.REJECTED

        offer.save()

        # Find linked workflow execution and resume if interrupted
        execution = WorkflowExecution.objects.filter(
            job=offer.application.job,
            workflow_type="recruitment",
        ).first()

        if execution and execution.status == WorkflowStatus.INTERRUPTED:
            WorkflowOrchestrationService.resume_recruitment_workflow(
                execution=execution,
                resume_data={
                    "candidate_response": resp,
                    "counter_salary": float(counter_salary) if counter_salary else None,
                    "negotiation_notes": notes,
                },
                user=request.user,
            )

        return Response(OfferSerializer(offer).data, status=status.HTTP_200_OK)


class OnboardingTaskViewSet(viewsets.ModelViewSet):
    """ViewSet for candidate onboarding checklist tasks."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OnboardingTaskSerializer

    def _get_user_org_ids(self):
        return OrganizationMembership.objects.filter(
            user=self.request.user,
            is_active=True,
        ).values_list("organization_id", flat=True)

    def get_queryset(self):
        org_ids = self._get_user_org_ids()
        return (
            OnboardingTask.objects.filter(organization_id__in=org_ids)
            .select_related("organization", "application", "application__candidate")
            .order_by("created_at")
        )

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get("status")
        if new_status in OnboardingTaskStatus.values:
            task.status = new_status
            if new_status == OnboardingTaskStatus.COMPLETED:
                task.completed_at = timezone.now()
            task.save()
            return Response(OnboardingTaskSerializer(task).data, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)


class JobPublicationViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for job board publication statuses."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = JobPublicationSerializer

    def _get_user_org_ids(self):
        return OrganizationMembership.objects.filter(
            user=self.request.user,
            is_active=True,
        ).values_list("organization_id", flat=True)

    def get_queryset(self):
        org_ids = self._get_user_org_ids()
        return JobPublication.objects.filter(job__organization_id__in=org_ids).select_related("job")


class WorkflowStatusView(APIView):
    """
    GET /api/v1/workflows/<thread_id>/status/
    Retrieve workflow execution state and timeline events.
    Guarded by organisation membership.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, thread_id: str):
        execution = get_object_or_404(
            WorkflowExecution.objects.select_related("job__organization").prefetch_related("events"),
            thread_id=thread_id,
        )

        is_member = OrganizationMembership.objects.filter(
            organization=execution.job.organization,
            user=request.user,
            is_active=True,
        ).exists()

        if not is_member:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = WorkflowExecutionSerializer(execution)
        return Response(serializer.data, status=status.HTTP_200_OK)
