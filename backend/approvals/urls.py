from django.urls import include, path
from rest_framework.routers import DefaultRouter

from approvals.views import ApprovalRequestViewSet

router = DefaultRouter()
router.register(r"", ApprovalRequestViewSet, basename="approval")

urlpatterns = [
    path("", include(router.urls)),
]
