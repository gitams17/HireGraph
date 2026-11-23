"""
Organisation-scoped permission helpers.

Pattern: views call get_membership() first, then check the returned role
against the relevant frozenset from models.py instead of hard-coding strings.
"""

from .models import MANAGEMENT_ROLES, OrganizationMembership, OrganizationRole


def get_membership(user, organization) -> OrganizationMembership | None:
    """Return the active membership record or None."""
    return OrganizationMembership.objects.filter(
        organization=organization, user=user, is_active=True
    ).first()


def is_member(user, organization) -> bool:
    return get_membership(user, organization) is not None


def is_manager(user, organization) -> bool:
    m = get_membership(user, organization)
    return m is not None and m.role in MANAGEMENT_ROLES


def is_owner(user, organization) -> bool:
    m = get_membership(user, organization)
    return m is not None and m.role == OrganizationRole.OWNER
