from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    """Return app and database health without exposing internal errors."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return JsonResponse(
            {"status": "error", "database": "unavailable"},
            status=503,
        )

    return JsonResponse({"status": "ok", "database": "connected"})
