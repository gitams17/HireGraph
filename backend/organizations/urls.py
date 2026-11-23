from django.urls import path

from .views import (
    InvitationListCreateView,
    MemberDetailView,
    MemberListView,
    OrganizationDetailView,
    OrganizationListCreateView,
)

urlpatterns = [
    path("", OrganizationListCreateView.as_view(), name="organization-list-create"),
    path("<uuid:org_id>/", OrganizationDetailView.as_view(), name="organization-detail"),
    path("<uuid:org_id>/members/", MemberListView.as_view(), name="organization-members"),
    path(
        "<uuid:org_id>/members/<uuid:member_id>/",
        MemberDetailView.as_view(),
        name="organization-member-detail",
    ),
    path(
        "<uuid:org_id>/invitations/",
        InvitationListCreateView.as_view(),
        name="organization-invitations",
    ),
]
