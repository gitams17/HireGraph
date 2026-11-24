from django.contrib import admin
from django.urls import include, path

from core.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    # Infrastructure
    path("api/health/", health_check, name="health-check"),
    # API v1
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/organizations/", include("organizations.urls")),
    path("api/v1/jobs/", include("jobs.urls")),
    path("api/v1/approvals/", include("approvals.urls")),
    path("api/v1/workflows/", include("workflows.urls")),
    path("api/v1/candidates/", include("candidates.urls")),
    path("api/v1/applications/", include("applications.urls")),
    path("api/v1/interviews/", include("interviews.urls")),
]
