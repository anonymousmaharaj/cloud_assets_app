"""Module containing functions for interaction with database."""

from contextlib import contextmanager
import logging
import os

from typing import List, Tuple

from celery_settings import celery_app
import psycopg2
from psycopg2.extensions import cursor

logger = logging.getLogger(__name__)


@contextmanager
def get_cursor() -> cursor:
    """Return the cursor generator for database access."""
    with psycopg2.connect(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')) as conn:
        with conn.cursor() as db_cursor:
            yield db_cursor


def get_schedule_subscribers(schedule_id: int) -> List[int]:
    """
    Get all users who are subscribed to a certain periodicity of receiving reports.

    Args:
        schedule_id: Schedule identifier to get users with.

    Returns:
        (list): List containing user_id, e.g. [5, 1].

    """
    with get_cursor() as db_cursor:
        query = """
            SELECT user_id
              FROM assets_reportsubscribers
             WHERE schedule_id = %(schedule_id)s
        """
        db_cursor.execute(query, {'schedule_id': schedule_id})
        return [user[0] for user in db_cursor.fetchall()]


@celery_app.task
def get_rows(user_id: int) -> List[Tuple[str, int]]:
    """
    Receive a list of file extensions with their number for a particular user.

    Args:
        user_id: User identifier from database.

    Returns:
        (list): List of tuples containing file's extensions and count, e.g [('.jpg', 5), ('.exe', 2)].

    """
    query = """
            SELECT extension, count(extension)
              FROM assets_file
             WHERE owner_id = %(user_id)s
          GROUP BY extension;
    """
    with get_cursor() as db_cursor:
        try:
            db_cursor.execute(query, {'user_id': user_id})
            return db_cursor.fetchall()
        except psycopg2.Error as error:
            logger.error(f'Postgres error: {error}')
            raise error
