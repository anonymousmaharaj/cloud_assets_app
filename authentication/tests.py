"""Tests for s3 methods of Assets application."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from assets import forms


class TestAuthApp(TestCase):
    """TestCase class for testing File model."""

    def setUp(self) -> None:
        """Set default values for each test."""
        self.user = User.objects.create_user(username='test_user',
                                             password='test',
                                             email='test@test.test')
        self.credentials = {
            'username': 'test_user',
            'password': 'test'

        }

    def test_request_get(self):
        """Test move_file view's request with GET method."""
        response = self.client.get(reverse('login'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')

    def test_rename_folder_view_with_form(self):
        """Test move_file view's request with form."""
        form_data = {
            'new_folder': self.folder.pk
        }
        form = forms.UserRegisterForm(data=form_data, user=self.user)
        response = self.client.post(f'/move/?file={self.file.pk}', data=form_data,
                                    follow=True)
        self.assertTrue(form.is_valid())
        self.assertEqual(response.status_code, 200)
