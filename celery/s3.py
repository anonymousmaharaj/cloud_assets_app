"""Module containing functions for interaction with S3."""

import datetime
import logging
import os
from typing import BinaryIO

import boto3
from boto3.resources.factory import ServiceResource
from botocore.config import Config
from botocore.exceptions import ClientError

from celery_settings import celery_app

logger = logging.getLogger(__name__)


def get_bucket() -> ServiceResource:
    """
    Get the bucket from S3 with boto3.

    Returns:
        S3 Bucket object.
    """
    credentials = {
        'aws_access_key_id': os.getenv('AWS_KEY'),
        'aws_secret_access_key': os.getenv('AWS_SECRET_KEY')
    }
    config = Config(signature_version=os.getenv('AWS_SIGNATURE_VERSION'),
                    region_name=os.getenv('AWS_REGION'))

    return boto3.resource('s3', **credentials, config=config).Bucket(
        name=os.getenv('S3_BUCKET'))


@celery_app.task
def upload_excel_to_bucket(data: BinaryIO, user: int) -> None:
    """
    Generate key for s3 bucket and upload report.

    Args:
        data: Excel file.
        user: User identifier from db.
    """
    bucket = get_bucket()
    now = datetime.datetime.now()
    key = f'reports/{user}/{now}.xls'

    try:
        bucket.put_object(Body=data,
                          Bucket=bucket.name,
                          Key=key, )

    except ClientError as error:
        logger.error(f'user_id: {user}. Error while upload report.')
        raise error
