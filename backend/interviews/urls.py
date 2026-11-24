from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InterviewTemplateViewSet, InterviewViewSet

router = DefaultRouter()
router.register(r"templates", InterviewTemplateViewSet, basename="interview-template")
router.register(r"", InterviewViewSet, basename="interview")

urlpatterns = [
    path("", include(router.urls)),
]
