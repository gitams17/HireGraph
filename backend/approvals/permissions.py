from organizations.models import OrganizationMembership

CAN_APPROVE_JOBS: frozenset[str] = frozenset({"owner", "admin", "hiring_manager"})


def get_approval_membership(user, organization) -> OrganizationMembership | None:
    return OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        is_active=True,
    ).first()
