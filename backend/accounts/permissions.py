"""
Account-level permission helpers.

Organisation-scoped permissions (membership roles, etc.) are defined in
organizations/permissions.py.  The views in this app use DRF's built-in
IsAuthenticated / AllowAny directly.
"""
# Nothing custom is needed here yet; kept as an explicit module so the
# pattern is established for future account-level rules (e.g. email-verified).
