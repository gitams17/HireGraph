from django.contrib import admin

from .models import Organization, OrganizationInvitation, OrganizationMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_by", "created_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "slug", "created_at", "updated_at"]
    ordering = ["name"]


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "role", "is_active", "joined_at"]
    list_filter = ["role", "is_active"]
    search_fields = ["user__email", "organization__name"]
    readonly_fields = ["id", "joined_at"]


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "organization", "role", "invited_by", "created_at", "accepted_at"]
    list_filter = ["role"]
    search_fields = ["email", "organization__name"]
    readonly_fields = ["id", "token", "created_at"]
