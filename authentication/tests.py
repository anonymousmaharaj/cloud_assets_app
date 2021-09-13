"""Tests for s3 methods of Assets application."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


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

    def test_register(self):
        """Test move_file view's request with form."""
        data = {
            'username': 'new_register',
            'email': 'newregistertest@test.com',
            'password1': 'VeryStrongPSWDFo0Test!',
            'password2': 'VeryStrongPSWDFo0Test!'
        }

        response = self.client.post(reverse('register'), data=data,
                                    follow=True)
        users = User.objects.all()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(users.count(), 2)
