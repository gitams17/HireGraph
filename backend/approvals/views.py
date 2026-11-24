from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from approvals.models import ApprovalRequest, ApprovalStatus
from approvals.permissions import CAN_APPROVE_JOBS, get_approval_membership
from approvals.serializers import ApprovalRequestSerializer, DecisionSerializer
from organizations.models import OrganizationMembership


class ApprovalRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ApprovalRequest.
    - list/retrieve: any active member of the organization.
    - decide: action='approve'|'reject' with optional feedback. Only owner, admin, hiring_manager.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApprovalRequestSerializer

    def get_queryset(self):
        user = self.request.user
        org_ids = OrganizationMembership.objects.filter(
            user=user, is_active=True
        ).values_list("organization_id", flat=True)

        qs = ApprovalRequest.objects.filter(organization_id__in=org_ids).select_related(
            "organization", "job", "version", "requested_by", "reviewed_by"
        )

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        job_param = self.request.query_params.get("job")
        if job_param:
            qs = qs.filter(job_id=job_param)

        return qs

    @action(detail=True, methods=["post"], url_path="decide")
    def decide(self, request, pk=None):
        serializer = DecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision_action = serializer.validated_data["action"]
        feedback = serializer.validated_data.get("feedback", "")

        with transaction.atomic():
            approval_request = self.get_object()

            # Verify permissions
            membership = get_approval_membership(request.user, approval_request.organization)
            if not membership or membership.role not in CAN_APPROVE_JOBS:
                raise PermissionDenied("You do not have permission to approve or reject job descriptions in this organisation.")

            # Double-action prevention
            if approval_request.status != ApprovalStatus.PENDING:
                raise ValidationError({"detail": f"This approval request has already been {approval_request.status}."})

            # Update business record
            is_approved = decision_action == "approve"
            approval_request.status = ApprovalStatus.APPROVED if is_approved else ApprovalStatus.REJECTED
            approval_request.reviewed_by = request.user
            approval_request.feedback = feedback
            approval_request.decided_at = timezone.now()
            approval_request.save()

            # Update version and job requisition records
            version = approval_request.version
            version.status = "approved" if is_approved else "rejected"
            version.save()

            if is_approved:
                job = approval_request.job
                job.status = "open"
                job.save()

            # Resume LangGraph workflow if active
            from workflows.services import WorkflowOrchestrationService
            thread_id = f"job-{approval_request.job_id}-jd"
            try:
                WorkflowOrchestrationService.resume_job_description_workflow(
                    thread_id=thread_id,
                    decision="approved" if is_approved else "rejected",
                    feedback=feedback,
                    user=request.user,
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Could not resume workflow for thread %s: %s", thread_id, e)

        return Response(ApprovalRequestSerializer(approval_request).data, status=status.HTTP_200_OK)
