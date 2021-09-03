"""Any API methods with AWS S3."""

import os

import boto3
from django.conf import settings


def create_bucket():
    """Create instance of Bucket."""
    conf = {
        'aws_access_key_id': settings.AWS_KEY,
        'aws_secret_access_key': settings.AWS_SECRET_KEY
    }
    return boto3.resource('s3', **conf).Bucket(name=settings.S3_BUCKET)


def upload_file(file_name, user, object_name=None, ):
    """Upload file to AWS S3 Bucket."""
    bucket = create_bucket()

    if object_name is None:
        object_name = os.path.basename(file_name)

    if not check_exist(bucket, object_name, user):
        with open(file_name, 'rb') as file:
            bucket.put_object(Body=file,
                              Bucket=bucket.name,
                              Key=f'{user.username}/{object_name}')
        if check_exist(bucket, object_name, user):
            return True
        else:
            return False
    else:
        return False


def check_exist(bucket, object_name, user):
    """Check file's exist in current directory."""
    response = list(bucket.objects.filter(
        Prefix=f'{user.username}/{object_name}'))
    return True if len(response) > 0 else False
