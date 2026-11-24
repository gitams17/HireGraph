from django.contrib import admin

from .models import JobRequisition


@admin.register(JobRequisition)
class JobRequisitionAdmin(admin.ModelAdmin):
    list_display = ["title", "organization", "status", "employment_type", "created_at"]
    list_filter = ["status", "employment_type", "organization"]
    search_fields = ["title", "department", "location"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
