"""Module containing Celery settings."""
import enum
import os

from celery import Celery
from celery.schedules import crontab


class Schedules(enum.Enum):
    """A class for defining schedules id."""

    daily = 1
    weekly = 2
    monthly = 3


celery_app = Celery('tasks', broker=os.getenv('BROKER_URL'))

celery_app.conf.beat_schedule = {
    'daily': {
        'task': 'tasks.get_subscribed_users',
        'schedule': 60,
        'args': (Schedules.daily.value,)
    },
    'weekly': {
        'task': 'tasks.get_subscribed_users',
        'schedule': crontab(minute=0, hour=0, day_of_week='sun'),
        'args': (Schedules.weekly.value,)
    },
    'monthly': {
        'task': 'tasks.get_subscribed_users',
        'schedule': crontab(minute=0, hour=0, day_of_month='1'),
        'args': (Schedules.monthly.value,)
    },
}
