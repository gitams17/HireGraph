from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.models import OrganizationMembership
from workflows.models import WorkflowExecution
from workflows.serializers import WorkflowExecutionSerializer


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

        # Enforce org membership
        is_member = OrganizationMembership.objects.filter(
            organization=execution.job.organization,
            user=request.user,
            is_active=True,
        ).exists()

        if not is_member:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = WorkflowExecutionSerializer(execution)
        return Response(serializer.data, status=status.HTTP_200_OK)
