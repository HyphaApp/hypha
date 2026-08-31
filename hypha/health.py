import logging

from django.db import OperationalError, connection
from django.http import HttpResponse, HttpResponseServerError

logger = logging.getLogger(__name__)


def health(request):
    """Lightweight health check used by Docker and load balancers.

    Returns 200 when the application and database are reachable.
    Returns 500 if the database cannot be reached.
    """
    try:
        connection.ensure_connection()
    except OperationalError as e:
        logger.exception("Health check failed: %s", e)
        return HttpResponseServerError("failed", content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")
