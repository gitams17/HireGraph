from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.models import Organization, OrganizationMembership

from .filters import JobRequisitionFilter
from .models import JobRequisition
from .permissions import CAN_MANAGE_JOBS, get_job_membership
from .serializers import (
    JobRequisitionDetailSerializer,
    JobRequisitionListSerializer,
    JobRequisitionWriteSerializer,
)


class JobPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class JobRequisitionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for JobRequisition CRUD.

    - List/Retrieve: any active member of the organization(s) the user belongs to.
    - Create/Update/Delete: roles in CAN_MANAGE_JOBS (owner, admin, recruiter).
    - Non-members attempting access receive 404 (enumeration prevention).
    - Filtering: status, department, location, employment_type (DjangoFilterBackend).
    - Search: title, department (SearchFilter).
    - Ordering: -created_at (default), created_at, title.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = JobPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobRequisitionFilter
    search_fields = ["title", "department"]
    ordering_fields = ["created_at", "title", "status"]
    ordering = ["-created_at"]

    # ------------------------------------------------------------------
    # Queryset helpers
    # ------------------------------------------------------------------

    def _get_user_org_ids(self):
        """Return UUIDs of all orgs where the current user is an active member."""
        return OrganizationMembership.objects.filter(
            user=self.request.user,
            is_active=True,
        ).values_list("organization_id", flat=True)

    def get_queryset(self):
        return (
            JobRequisition.objects.filter(
                organization_id__in=self._get_user_org_ids()
            )
            .select_related("organization", "created_by")
        )

    # ------------------------------------------------------------------
    # Serializer selection
    # ------------------------------------------------------------------

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return JobRequisitionWriteSerializer
        if self.action == "list":
            return JobRequisitionListSerializer
        return JobRequisitionDetailSerializer

    # ------------------------------------------------------------------
    # Permission helpers
    # ------------------------------------------------------------------

    def _get_org_or_404(self, org_id: str) -> Organization:
        """Return org if user is an active member, else 404."""
        return get_object_or_404(
            Organization,
            id=org_id,
            memberships__user=self.request.user,
            memberships__is_active=True,
        )

    def _require_manage_permission(self, organization: Organization) -> None:
        """Raise 403 if user lacks job management rights for the given org."""
        membership = get_job_membership(self.request.user, organization)
        if membership is None or membership.role not in CAN_MANAGE_JOBS:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to manage jobs in this organisation.")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        org_id = request.data.get("organization")
        if not org_id:
            return Response(
                {"organization": ["This field is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        organization = self._get_org_or_404(org_id)
        self._require_manage_permission(organization)

        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        job = write_serializer.save(
            organization=organization,
            created_by=request.user,
        )
        read_serializer = JobRequisitionDetailSerializer(job, context=self.get_serializer_context())
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        self._require_manage_permission(instance.organization)

        write_serializer = self.get_serializer(instance, data=request.data, partial=partial)
        write_serializer.is_valid(raise_exception=True)
        job = write_serializer.save()
        read_serializer = JobRequisitionDetailSerializer(job, context=self.get_serializer_context())
        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self._require_manage_permission(instance.organization)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
