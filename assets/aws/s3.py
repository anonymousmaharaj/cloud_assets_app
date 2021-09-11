"""Any API methods with AWS S3."""

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

from assets import models
from assets.db import queries


def create_bucket():
    """Create instance of Bucket."""
    conf = {
        'aws_access_key_id': settings.AWS_KEY,
        'aws_secret_access_key': settings.AWS_SECRET_KEY
    }
    return boto3.resource('s3', **conf).Bucket(name=settings.S3_BUCKET)


def get_url(file_id):
    """Get url for download file."""
    file_obj = models.File.objects.get(pk=file_id)
    file_key = file_obj.relative_key
    full_url = f'https://{settings.S3_BUCKET}.s3.amazonaws.com/{file_key}'
    return full_url


def upload_file(file_name, key):
    """Upload file to AWS S3 Bucket."""
    bucket = create_bucket()

    try:
        bucket.put_object(Body=file_name,
                          Bucket=bucket.name,
                          Key=key,
                          ACL='public-read')

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


def delete_folders(folder_id):
    """Delete folder with files from S3."""
    delete_recursive(folder_id)


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
