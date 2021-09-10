"""Tests for models of Assets application."""

import os
import tempfile
import uuid

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from assets import models
from assets.db import queries


class TestFileModel(TestCase):
    """TestCase class for testing File model."""

    def setUp(self) -> None:
        user = User.objects.create(username='test_user')
        key = str(uuid.uuid4())
        temp_file = tempfile.NamedTemporaryFile()
        models.File(title=os.path.basename(temp_file.name),
                    owner=user,
                    folder=None,
                    relative_key=key).save()

    @property
    def get_current_id(self):
        file_exist = models.File.objects.exists()
        if file_exist:
            files = models.File.objects.filter()
            return files[0]

    def test_create_file_exist_name(self):
        user = User.objects.get(username='test_user')
        current_file = models.File.objects.get(pk=self.get_current_id.pk)
        try:
            models.File.objects.create(title=current_file.title,
                                       folder_id=None,
                                       relative_key=current_file.relative_key,
                                       owner=user)
        except IntegrityError:
            self.assertRaises(IntegrityError)

    def test_rename_file(self):
        unique_name = str(uuid.uuid4())
        current_file = models.File.objects.get(pk=self.get_current_id.pk)
        queries.rename_file(file_id=current_file.pk, new_title=unique_name)
        current_file = models.File.objects.get(pk=self.get_current_id.pk)
        self.assertEqual(current_file.title, unique_name)

    def test_delete_file(self):
        current_file = models.File.objects.get(pk=self.get_current_id.pk)
        queries.delete_file(file_id=current_file.pk)
        file_exist = models.File.objects.filter(pk=current_file.pk).exists()
        self.assertFalse(file_exist)


class TestFolderModel(TestCase):
    """TestCase class for testing Folder model."""

    def setUp(self) -> None:
        user = User.objects.create(username='test_user')
        title = str(uuid.uuid4())
        models.Folder(title=title,
                      owner=user,
                      parent=None).save()

    @property
    def get_current_id(self):
        folder_exist = models.Folder.objects.exists()
        if folder_exist:
            folders = models.Folder.objects.filter()
            return folders[0]

    def test_create_folder_exist_name(self):
        user = User.objects.get(username='test_user')
        current_folder = models.Folder.objects.get(pk=self.get_current_id.pk)
        try:
            models.Folder.objects.create(title=current_folder.title,
                                         parent_id=None,
                                         owner=user)
        except IntegrityError:
            self.assertRaises(IntegrityError)

    def test_rename_folder(self):
        unique_name = str(uuid.uuid4())
        current_folder = models.Folder.objects.get(pk=self.get_current_id.pk)
        queries.rename_folder(folder_id=current_folder.pk, new_title=unique_name)
        current_folder = models.Folder.objects.get(pk=self.get_current_id.pk)
        self.assertEqual(current_folder.title, unique_name)

    def test_delete_folder(self):
        current_folder = models.Folder.objects.get(pk=self.get_current_id.pk)
        queries.delete_recursive(folder_id=current_folder.pk)
        folder_exist = models.Folder.objects.filter(pk=current_folder.pk).exists()
        self.assertFalse(folder_exist)
