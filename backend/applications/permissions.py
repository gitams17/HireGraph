from organizations.models import OrganizationMembership

CAN_MANAGE_APPLICATIONS: frozenset[str] = frozenset({"owner", "admin", "recruiter"})
CAN_REVIEW_APPLICATIONS: frozenset[str] = frozenset({"owner", "admin", "recruiter", "hiring_manager"})


def get_application_membership(user, organization) -> OrganizationMembership | None:
    return OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        is_active=True,
    ).first()
