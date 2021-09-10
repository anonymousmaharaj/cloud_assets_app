"""Tests for views of Assets application."""

import uuid

from django.contrib.auth.models import User
from django.test import TestCase

from assets import models


class TestRootPage(TestCase):

    def setUp(self) -> None:
        user = User.objects.create(username='test_user')

        folder = models.Folder.objects.create(
            title='test_folder',
            owner=user,
            parent=None,
        )
        models.File.objects.create(
            title='test_file.txt',
            owner=user,
            folder=None,
            relative_key=(str(uuid.uuid4()))
        )
        models.File.objects.create(
            title='test_file.txt',
            owner=user,
            folder=folder,
            relative_key=(str(uuid.uuid4()))
        )

    def test_root_page(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 302)
