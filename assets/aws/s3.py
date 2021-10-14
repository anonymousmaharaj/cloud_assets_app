"""Any API methods with AWS S3."""
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings
from rest_framework.exceptions import ParseError

from assets import models
from assets.db import queries

logger = logging.getLogger(__name__)


def create_bucket():
    """Create instance of Bucket."""
    credentials = {
        'aws_access_key_id': settings.AWS_KEY,
        'aws_secret_access_key': settings.AWS_SECRET_KEY
    }
    config = Config(signature_version=settings.AWS_SIGNATURE_VERSION,
                    region_name=settings.AWS_REGION)

    return boto3.resource('s3', **credentials, config=config).Bucket(
        name=settings.S3_BUCKET)


def get_url(file_id):
    """Get url for download file."""
    bucket = create_bucket()

    file_obj = models.File.objects.get(pk=file_id)
    file_key = file_obj.relative_key
    params = {
        'Bucket': bucket.name,
        'Key': file_key,
        'ResponseContentDisposition': f'attachment; filename = {file_obj.title}'
    }
    response = bucket.meta.client.generate_presigned_url('get_object',
                                                         Params=params,
                                                         ExpiresIn=3600)
    return response


def upload_file(file_name, key, extension, content_type):
    """Upload file to AWS S3 Bucket."""
    bucket = create_bucket()

    try:
        bucket.put_object(Body=file_name,
                          Bucket=bucket.name,
                          Key=key,
                          ContentType=content_type,
                          Tagging=f'Extension={extension}')

    except ClientError:
        return False
    else:
        return True


def delete_key(file_id):
    """Delete file from S3."""
    bucket = create_bucket()
    file_obj = models.File.objects.get(pk=file_id)
    key = file_obj.relative_key
    # TODO: Fix validation.
    delete_dict = {
        'Objects': [
            {'Key': key}
        ]
    }
    try:
        bucket.delete_objects(Delete=delete_dict)
    except ClientError:
        return False
    else:
        return True


def delete_recursive(folder_id):
    """Find all children and delete them."""
    folders = models.Folder.objects.filter(parent=folder_id).exists()
    files = models.File.objects.filter(folder=folder_id)

    for file in files:
        delete_key(file.pk)
        queries.delete_file(file.pk)

    if folders:
        folders_qs = models.Folder.objects.filter(parent=folder_id)
        for folder in folders_qs:
            delete_recursive(folder.pk)
    models.Folder.objects.filter(pk=folder_id).delete()


def check_exists(key):
    """Check thumbnails exist."""
    bucket = create_bucket()
    s3 = boto3.client('s3')
    try:
        s3.head_object(Bucket=bucket.name, Key=key)
    except ClientError:
        logger.critical(f'Thumbnail does not exist. key = {key}')
        raise ParseError(f'Thumbnail does not exist. key = {key}')
