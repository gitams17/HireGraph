from organizations.models import OrganizationMembership

CAN_MANAGE_INTERVIEWS: frozenset[str] = frozenset({"owner", "admin", "recruiter"})
CAN_CONDUCT_INTERVIEWS: frozenset[str] = frozenset({"owner", "admin", "recruiter", "hiring_manager", "interviewer"})


def get_interview_membership(user, organization) -> OrganizationMembership | None:
    return OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        is_active=True,
    ).first()
