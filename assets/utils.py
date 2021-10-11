"""Additional utils for assets app."""

import logging
import uuid

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Handle exception with logs."""
    response = exception_handler(exc, context)

    if response is not None:
        response.data['status_code'] = response.status_code

    logger.error(str(exc))
    return response


def create_file_relative_key(user_id):
    """Generate unique key."""
    return f'users/{user_id}/assets/{uuid.uuid4()}'
