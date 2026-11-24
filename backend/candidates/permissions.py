from organizations.models import OrganizationMembership

CAN_MANAGE_CANDIDATES: frozenset[str] = frozenset({"owner", "admin", "recruiter"})


def get_candidate_membership(user, organization) -> OrganizationMembership | None:
    """Return active membership or None."""
    return OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        is_active=True,
    ).first()
