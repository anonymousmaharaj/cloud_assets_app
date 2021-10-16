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


def get_url(uuid):
    """Get url for download file."""
    bucket = create_bucket()

    file_obj = models.File.objects.filter(relative_key__contains=uuid).first()
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
    file_obj = models.File.objects.filter(relative_key__contains=file_id).first()
    key = file_obj.relative_key

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
    folders = models.Folder.objects.filter(parent__uuid=folder_id).exists()
    files = models.File.objects.filter(folder__uuid=folder_id)

    for file in files:
        uuid = file.relative_key.split('/')[-1]
        delete_key(uuid)
        queries.delete_shared_table(uuid)
        queries.delete_file(uuid)

    if folders:
        folders_qs = models.Folder.objects.filter(parent__uuid=folder_id)
        for folder in folders_qs:
            delete_recursive(folder.uuid)
    models.Folder.objects.get(uuid=folder_id).delete()


def check_exists(key):
    """Check thumbnails exist."""
    bucket = create_bucket()
    s3 = boto3.client('s3')
    try:
        s3.head_object(Bucket=bucket.name, Key=key)
    except ClientError:
        message = f'Thumbnail does not exist. key = {key}'
        logger.critical(message)
        raise ParseError(message)
