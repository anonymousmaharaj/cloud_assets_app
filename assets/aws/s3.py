"""Any API methods with AWS S3."""

import os

import boto3
from botocore import exceptions


def upload_file(file_name, object_name=None):
    """Upload file to AWS S3 Bucket."""
    s3_resource = boto3.resource('s3', aws_access_key_id=os.getenv('AWS_KEY'),
                                 aws_secret_access_key=os.getenv('AWS_SECRET_KEY'))
    bucket = s3_resource.Bucket(name=os.getenv('S3_BUCKET'))

    if object_name is None:
        object_name = os.path.basename(file_name)

    if not check_exist(s3_resource, bucket, object_name):
        with open(file_name, 'rb') as file:
            bucket.put_object(Body=file, Bucket=bucket.name, Key=object_name)
        if check_exist(s3_resource, bucket, object_name):
            return True
        else:
            return False
    else:
        return False


def check_exist(s3_resource, bucket, object_name):
    """Check file's exist in current directory."""
    try:
        s3_resource.Object(bucket.name, object_name).load()
    except exceptions.ClientError:
        return False
    else:
        return True
