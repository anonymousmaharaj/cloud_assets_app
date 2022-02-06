"""Module containing Sentry settings."""

import logging
import os

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[LoggingIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True,
)

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.WARNING
)

logger = logging.getLogger(__name__)
