import mimetypes
from pathlib import Path

from django.db.models import Count
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organizations.models import OrganizationMembership
from .filters import CandidateFilter
from .models import Candidate, Resume
from .permissions import CAN_MANAGE_CANDIDATES, get_candidate_membership
from .serializers import (
    CandidateDetailSerializer,
    CandidateListSerializer,
    CandidateWriteSerializer,
    ResumeSerializer,
    ResumeUploadSerializer,
)


class CandidatePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CandidateViewSet(viewsets.ModelViewSet):
    """
    CRUD and actions for Candidates.
    Tenant isolated: callers can only see/modify candidates from their active organisations.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CandidatePagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CandidateFilter
    search_fields = ["first_name", "last_name", "email", "current_company", "current_title"]
    ordering_fields = ["created_at", "first_name", "last_name", "email"]
    ordering = ["-created_at"]

    def _get_user_org_ids(self):
        return OrganizationMembership.objects.filter(
            user=self.request.user,
            is_active=True,
        ).values_list("organization_id", flat=True)

    def get_queryset(self):
        org_ids = self._get_user_org_ids()
        return (
            Candidate.objects.filter(organization_id__in=org_ids)
            .annotate(
                resume_count=Count("resumes", distinct=True),
                application_count=Count("applications", distinct=True),
            )
            .prefetch_related("resumes", "applications__job")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return CandidateListSerializer
        if self.action == "retrieve":
            return CandidateDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return CandidateWriteSerializer
        return CandidateDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate = serializer.save(created_by=request.user)
        return Response(
            CandidateDetailSerializer(candidate).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        candidate = self.get_object()
        membership = get_candidate_membership(request.user, candidate.organization)
        if not membership or membership.role not in CAN_MANAGE_CANDIDATES:
            return Response(
                {"detail": "You do not have permission to delete candidates in this organisation."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="resumes")
    def upload_resume(self, request, pk=None):
        candidate = self.get_object()
        membership = get_candidate_membership(request.user, candidate.organization)
        if not membership or membership.role not in CAN_MANAGE_CANDIDATES:
            return Response(
                {"detail": "You do not have permission to upload resumes for this candidate."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ResumeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        is_primary = serializer.validated_data.get("is_primary", True)

        # Detect content type
        content_type = uploaded_file.content_type
        if not content_type or content_type == "application/octet-stream":
            guessed, _ = mimetypes.guess_type(uploaded_file.name)
            content_type = guessed or "application/pdf"

        resume = Resume.objects.create(
            candidate=candidate,
            file=uploaded_file,
            file_name=Path(uploaded_file.name).name,
            file_size=uploaded_file.size,
            content_type=content_type,
            is_primary=is_primary,
            uploaded_by=request.user,
        )

        return Response(ResumeSerializer(resume).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path=r"resumes/(?P<resume_id>[^/.]+)/download")
    def download_resume(self, request, pk=None, resume_id=None):
        candidate = self.get_object()
        # Active membership is already verified by get_object() via organization_id__in
        resume = get_object_or_404(Resume, id=resume_id, candidate=candidate)

        try:
            file_handle = resume.file.open("rb")
        except Exception:
            raise Http404("Resume file not found on storage.")

        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=resume.file_name,
            content_type=resume.content_type or "application/octet-stream",
        )
        return response
