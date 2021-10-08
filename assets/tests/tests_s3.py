"""Tests for s3 methods of Assets application."""
import tempfile
from unittest.mock import Mock, patch
import uuid

from django.contrib.auth.models import User
from django.test import TestCase

from assets import models
from assets.aws import s3


class TestS3Methods(TestCase):
    """TestCase class for testing s3 methods."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.relative_key = uuid.uuid4()
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.file = models.File.objects.create(title='test_file.txt',
                                               owner=self.user,
                                               folder=None,
                                               relative_key=self.relative_key,
                                               size=1024,
                                               extension='.txt')

    @patch('assets.aws.s3.create_bucket')
    def test_create_bucket(self, mock_create_bucket):
        """Test create bucket func."""
        mock_create_bucket.return_value = Mock()
        s3.create_bucket()

    @patch('assets.aws.s3.create_bucket')
    @patch('botocore.client.BaseClient._make_api_call')
    def test_upload_file(self, api_call, mock_bucket):
        """Test upload file func."""
        with tempfile.NamedTemporaryFile() as temp_file:
            mock_bucket.return_value = Mock()
            api_call.return_value = True
            response = s3.upload_file(temp_file.name, self.relative_key, 'txt', 'octet-stream')
            self.assertTrue(response)

    @patch('assets.aws.s3.create_bucket')
    @patch('botocore.client.BaseClient._make_api_call')
    def test_delete_file(self, api_call, mock_bucket):
        """Test delete file from bucket func."""
        mock_bucket.return_value = Mock()
        api_call.return_value = True
        response = s3.delete_key(self.file.pk)
        self.assertTrue(response)
