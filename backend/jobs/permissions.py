from organizations.models import OrganizationMembership

# Roles that can create, update and delete jobs
CAN_MANAGE_JOBS: frozenset[str] = frozenset({"owner", "admin", "recruiter"})


def get_job_membership(user, organization) -> OrganizationMembership | None:
    """Return active membership or None."""
    return OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        is_active=True,
    ).first()
