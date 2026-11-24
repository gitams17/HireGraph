from django.urls import include, path
from rest_framework.routers import DefaultRouter

from workflows.views import (
    JobPublicationViewSet,
    OfferViewSet,
    OnboardingTaskViewSet,
    WorkflowStatusView,
    WorkflowViewSet,
)

router = DefaultRouter()
router.register(r"offers", OfferViewSet, basename="offer")
router.register(r"onboarding", OnboardingTaskViewSet, basename="onboarding")
router.register(r"publications", JobPublicationViewSet, basename="job-publication")
router.register(r"", WorkflowViewSet, basename="workflow")

urlpatterns = [
    path("<str:thread_id>/status/", WorkflowStatusView.as_view(), name="workflow-status"),
    path("", include(router.urls)),
]
