import io
import os
import requests
import urllib.parse

import boto3
from PIL import Image

print('Loading function')

s3 = boto3.client('s3')

img_extensions = ['.jpg', '.png', '.bmp']

host = os.getenv('CLOUD_HOST')


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    try:
        tags = s3.get_object_tagging(Bucket=bucket, Key=key)
        if tags['TagSet'][0]['Value'] not in img_extensions:
            print('Is not image')
            return response['ContentType']    # noqa

        file = s3.get_object(Bucket=bucket, Key=key)

        thumbnail_key = f'thumbnails/{key}'

        with Image.open(file['Body']) as f:
            f.thumbnail((256, 256))
            mem_file = io.BytesIO()
            f.save(mem_file, format=f.format)
            mem_file.seek(0)
            s3.put_object(Bucket=bucket, Key=thumbnail_key, Body=mem_file)

        requests.post(
            f'{host}/api/assets/files/thumbnail/{key.split("/")[-1]}/',
            data={'thumbnail_key': thumbnail_key})

        print('CONTENT TYPE: ' + response['ContentType'])
        return response['ContentType']    # noqa
    except Exception as e:
        print(e)
        print(
            f'Error getting object {key} from bucket {bucket}. '
            'Make sure they exist and your bucket is in the same region as this function.'
        )
        raise e
