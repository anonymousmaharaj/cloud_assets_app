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
        """Set default values for each test."""
        self.user = User.objects.create(username='test_user')
        key = str(uuid.uuid4())
        temp_file = tempfile.NamedTemporaryFile()
        models.File(title=os.path.basename(temp_file.name),
                    owner=self.user,
                    folder=None,
                    relative_key=key,
                    extension='.txt',
                    size=1024).save()

    @property
    def get_current_id(self):
        """Auxiliary func for tests."""
        if models.File.objects.exists():
            files = models.File.objects.filter()
            return files[0]

    def test_create_file_exist_name(self):
        """Test create file with exist name."""
        current_file = models.File.objects.get(pk=self.get_current_id.pk)
        try:
            models.File.objects.create(title=current_file.title,
                                       folder_id=None,
                                       relative_key=current_file.relative_key,
                                       owner=self.user,
                                       extension='.txt',
                                       size=1024
                                       )
        except IntegrityError:
            self.assertRaises(IntegrityError)

    def test_rename_file(self):
        """Test rename file."""
        unique_name = str(uuid.uuid4())
        current_file = models.File.objects.get(pk=self.get_current_id.pk)
        queries.rename_file(file_id=current_file.pk, new_title=unique_name)
        current_file = models.File.objects.get(pk=self.get_current_id.pk)
        self.assertEqual(current_file.title, unique_name)

    def test_rename_file_with_exist_name(self):
        """Test rename file with exist name."""
        current_file = models.File.objects.get(pk=self.get_current_id.pk)
        queries.rename_file(file_id=current_file.pk, new_title=current_file.title)
        current_file = models.File.objects.get(pk=self.get_current_id.pk)
        try:
            self.assertEqual(current_file.title, current_file.title)
        except IntegrityError:
            self.assertRaises(IntegrityError)

    def test_delete_file(self):
        """Test delete file."""
        current_file = models.File.objects.get(pk=self.get_current_id.pk)
        queries.delete_file(file_id=current_file.pk)
        file_exist = models.File.objects.filter(pk=current_file.pk).exists()
        self.assertFalse(file_exist)


class TestFolderModel(TestCase):
    """TestCase class for testing Folder model."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create(username='test_user')
        title = str(uuid.uuid4())
        models.Folder(title=title,
                      owner=self.user,
                      parent=None).save()

    @property
    def get_current_id(self):
        """Auxiliary func for tests."""
        folder_exist = models.Folder.objects.exists()
        if folder_exist:
            folders = models.Folder.objects.filter()
            return folders[0]

    def test_create_folder_exist_name(self):
        """Test create folder with exist name."""
        current_folder = models.Folder.objects.get(pk=self.get_current_id.pk)
        try:
            models.Folder.objects.create(title=current_folder.title,
                                         parent_id=None,
                                         owner=self.user)
        except IntegrityError:
            self.assertRaises(IntegrityError)

    def test_rename_folder(self):
        """Test rename folder."""
        unique_name = str(uuid.uuid4())
        current_folder = models.Folder.objects.get(pk=self.get_current_id.pk)
        queries.rename_folder(folder_id=current_folder.pk,
                              new_title=unique_name)
        current_folder = models.Folder.objects.get(pk=self.get_current_id.pk)
        self.assertEqual(current_folder.title, unique_name)

    def test_rename_folder_with_exist_name(self):
        """Test rename folder with exist name."""
        unique_name = str(uuid.uuid4())
        current_folder = models.Folder.objects.get(pk=self.get_current_id.pk)
        queries.rename_folder(folder_id=current_folder.pk,
                              new_title=unique_name)
        current_folder = models.Folder.objects.get(pk=self.get_current_id.pk)
        try:
            self.assertEqual(current_folder.title, current_folder.title)
        except IntegrityError:
            self.assertRaises(IntegrityError)

    def test_delete_folder(self):
        """Test delete folders."""
        current_folder = models.Folder.objects.get(pk=self.get_current_id.pk)
        queries.delete_recursive(folder_id=current_folder.pk)
        folder_exist = models.Folder.objects.filter(pk=current_folder.pk).exists()
        self.assertFalse(folder_exist)
