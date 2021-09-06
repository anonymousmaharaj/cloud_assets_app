"""Any API methods with AWS S3."""

import os

import boto3
from django.conf import settings

from assets import models


def create_bucket():
    """Create instance of Bucket."""
    conf = {
        'aws_access_key_id': settings.AWS_KEY,
        'aws_secret_access_key': settings.AWS_SECRET_KEY
    }
    return boto3.resource('s3', **conf).Bucket(name=settings.S3_BUCKET)


def create_path(user, parent_folder):
    """Create full path for upload file."""
    if parent_folder is None:
        return user.username

    path_objects = []

    while parent_folder.parent is not None:
        parent_folder = models.Folder.objects.get(pk=parent_folder.parent.pk)
        path_objects.append(parent_folder.title)
    path_objects.reverse()
    full_path = os.path.join(user.username, *path_objects)
    return full_path


def upload_file(file_name, user, parent_folder, object_name=None, ):
    """Upload file to AWS S3 Bucket."""
    bucket = create_bucket()

    if object_name is None:
        object_name = os.path.basename(file_name)

    new_path = create_path(user, parent_folder)

    if not check_exist(bucket, object_name, new_path):
        with open(file_name, 'rb') as file:

            bucket.put_object(Body=file,
                              Bucket=bucket.name,
                              Key=f'{new_path}/'
                                  f'{object_name}',
                              ACL='public-read')
        if check_exist(bucket, object_name, new_path):
            return True
        else:
            return False
    else:
        return False


def check_exist(bucket, object_name, path):
    """Check file's exist in current directory."""
    response = list(bucket.objects.filter(
        Prefix=f'{path}/{object_name}'))
    return True if len(response) > 0 else False
