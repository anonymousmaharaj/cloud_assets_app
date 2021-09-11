"""Tests for views of Assets application."""

import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from assets import forms
from assets import models


class TestRootPageView(TestCase):
    """Tests for root_page view."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.credentials = {
            'username': 'test_user',
            'password': 'test'
        }

        folder = models.Folder.objects.create(
            title='test_folder',
            owner=self.user,
            parent=None,
        )
        models.File.objects.create(
            title='test_file.txt',
            owner=self.user,
            folder=None,
            relative_key=(str(uuid.uuid4()))
        )
        models.File.objects.create(
            title='test_file.txt',
            owner=self.user,
            folder=folder,
            relative_key=(str(uuid.uuid4()))
        )

    def test_root_page_with_auth_get(self):
        """Test root page with authentication."""
        self.client.login(**self.credentials)
        response = self.client.get(reverse('root_page'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/root_page.html')

    def test_root_page_without_auth_get(self):
        """Test root page without authentication."""
        response = self.client.get(reverse('root_page'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/login.html')


class TestUploadFileView(TestCase):
    """Tests for upload_file view."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.credentials = {
            'username': 'test_user',
            'password': 'test'
        }
        self.client.login(**self.credentials)

    def test_request_get(self):
        """Test upload_file view's request with GET method."""
        response = self.client.get(reverse('upload_file'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/upload_file.html')

    def test_upload_file_view_with_form(self):
        """Test upload_file view's request with form."""
        form_data = {
            'path': 'test/test/test.txt',
        }
        form = forms.UploadFileForm(data=form_data)
        response = self.client.post('/upload_file/', data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(response.status_code, 200)


class TestCreateFolderView(TestCase):
    """Tests for create_folder view."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.credentials = {
            'username': 'test_user',
            'password': 'test'
        }
        self.client.login(**self.credentials)

    def test_request_get(self):
        """Test create_folder view's request with GET method."""
        response = self.client.get(reverse('create_folder'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/create_folder.html')

    def test_create_folder_view_with_form(self):
        """Test create_folder view's request with form."""
        form_data = {
            'title': 'test-folder',
        }
        form = forms.CreateFolderForm(data=form_data)
        response = self.client.post('/create-folder/', data=form_data, follow=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(response.status_code, 200)


class TestRenameFolderView(TestCase):
    """Tests for rename_folder view."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.credentials = {
            'username': 'test_user',
            'password': 'test'
        }
        self.client.login(**self.credentials)
        self.folder = models.Folder.objects.create(
            title='test_folder',
            owner=self.user,
            parent=None,
        )
        self.get_params = {
            'folder': self.folder.pk
        }

    def test_request_get(self):
        """Test rename_folder view's request with GET method."""
        response = self.client.get(reverse('rename_folder'), follow=True, data=self.get_params)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/rename_folder.html')

    def test_rename_folder_view_with_form(self):
        """Test rename_folder view's request with form."""
        form_data = {
            'new_title': 'test',
        }
        form = forms.RenameFolderForm(data=form_data)
        response = self.client.post(f'/rename-folder/?folder={self.folder.pk}', data=form_data,
                                    follow=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(response.status_code, 200)


class TestRenameFileView(TestCase):
    """Tests for rename_file view."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.credentials = {
            'username': 'test_user',
            'password': 'test'
        }
        self.client.login(**self.credentials)
        self.folder = models.Folder.objects.create(
            title='test_folder',
            owner=self.user,
            parent=None,
        )
        self.file = models.File.objects.create(
            title='test_file.txt',
            owner=self.user,
            folder=None,
            relative_key=(str(uuid.uuid4()))
        )
        self.get_params = {
            'file': self.file.pk
        }

    def test_request_get(self):
        """Test rename_file view's request with GET method."""
        response = self.client.get(reverse('rename_file'), follow=True, data=self.get_params)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/rename_file.html')

    def test_rename_folder_view_with_form(self):
        """Test rename_file view's request with form."""
        form_data = {
            'new_title': 'test.jpg',
        }
        form = forms.RenameFileForm(data=form_data)
        response = self.client.post(f'/rename-file/?file={self.file.pk}', data=form_data,
                                    follow=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(response.status_code, 200)


class TestMoveFileView(TestCase):
    """Tests for move_file view."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.credentials = {
            'username': 'test_user',
            'password': 'test'
        }
        self.client.login(**self.credentials)
        self.folder = models.Folder.objects.create(
            title='test_folder',
            owner=self.user,
            parent=None,
        )
        self.file = models.File.objects.create(
            title='test_file.txt',
            owner=self.user,
            folder=None,
            relative_key=(str(uuid.uuid4()))
        )
        self.get_params = {
            'file': self.file.pk
        }

    def test_request_get(self):
        """Test move_file view's request with GET method."""
        response = self.client.get(reverse('move_file'), follow=True, data=self.get_params)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'assets/move_file.html')

    def test_rename_folder_view_with_form(self):
        """Test move_file view's request with form."""
        form_data = {
            'new_folder': self.folder.pk
        }
        form = forms.MoveFileForm(data=form_data, user=self.user)
        response = self.client.post(f'/move/?file={self.file.pk}', data=form_data,
                                    follow=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(response.status_code, 200)


class TestDeleteFileView(TestCase):
    """Tests for delete_file view."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.credentials = {
            'username': 'test_user',
            'password': 'test'
        }
        self.client.login(**self.credentials)

        self.file = models.File.objects.create(
            title='test_file.txt',
            owner=self.user,
            folder=None,
            relative_key=(str(uuid.uuid4()))
        )
        self.get_params = {
            'file': self.file.pk
        }

    def test_request_get(self):
        """Test move_file view's request with GET method."""
        response = self.client.get(reverse('delete_file'), follow=True, data=self.get_params)
        self.assertEqual(response.status_code, 200)


class TestDeleteFolderView(TestCase):
    """Tests for delete_folder view."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.credentials = {
            'username': 'test_user',
            'password': 'test'
        }
        self.client.login(**self.credentials)

        self.folder = models.Folder.objects.create(
            title='test_folder',
            owner=self.user,
            parent=None,
        )
        self.get_params = {
            'folder': self.folder.pk
        }

    def test_request_get(self):
        """Test move_file view's request with GET method."""
        response = self.client.get(reverse('delete_folder'), follow=True, data=self.get_params)
        self.assertEqual(response.status_code, 200)


class TestDownloadFileView(TestCase):
    """Tests for download_file view."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.credentials = {
            'username': 'test_user',
            'password': 'test'
        }
        self.client.login(**self.credentials)

        self.file = models.File.objects.create(
            title='test_file.txt',
            owner=self.user,
            folder=None,
        )
        self.get_params = {
            'file': self.file.pk
        }

    def test_request_get(self):
        """Test move_file view's request with GET method."""
        response = self.client.get(reverse('download_file'), data=self.get_params)
        self.assertRedirects(response, 'https://django-cloud-assets.s3.amazonaws.com/',
                             fetch_redirect_response=False)
