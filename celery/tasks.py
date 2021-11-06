"""Module containing Celery tasks."""

import logging

from celery import chain

from celery_settings import celery_app
from queries import get_schedule_subscribers
from queries import get_rows
from utils import create_excel_file

logger = logging.getLogger(__name__)


@celery_app.task
def get_subscribed_users(schedule_id: int) -> None:
    """
    Task to receive a report and send it to the bucket on a periodicity basis.

    Args:
        schedule_id: Schedule ID to get users with.

    Returns:
        None

    """
    users = get_schedule_subscribers(schedule_id)

    if not users:
        message = 'No users for monthly reports.'
        logger.INFO(message)
        return

    for user in users:
        chain(get_rows.s(user) | create_excel_file.s(user)).apply_async()
