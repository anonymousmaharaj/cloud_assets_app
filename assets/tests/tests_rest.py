from tempfile import TemporaryFile

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from assets.models import Folder


class FolderCreateTests(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(username='test_user',
                                                  password='test',
                                                  email='test@test.test')

        self.test_user_2 = User.objects.create_user(username='test_user_2',
                                                    password='test',
                                                    email='test_2@test.test')
        self.client = APIClient()

        self.folder = Folder.objects.create(
            title='test_folder_1',
            owner=self.test_user_2,
            parent=None,
        )

    def test_create_folder_success(self):
        self.client.login(username='test_user', password='test')
        payload = {
            'title': '<script>XSS Attack</script>',
        }
        response = self.client.post(
            reverse('assets-api-folders'),
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Folder.objects.count(), 2)
        self.assertEqual(response.data['title'], 'XSS Attack')
        self.assertEqual(Folder.objects.filter(title='XSS Attack').first().owner, self.test_user)

    def test_create_folder_failed(self):
        payload = {
            'title': '<script>XSS Attack</script>',
        }
        response = self.client.post(
            reverse('assets-api-folders'),
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_folder_wrong_field_failed(self):
        self.client.login(username='test_user', password='test')
        payload = {
            'wrong_field': '<script>XSS Attack</script>',
        }
        response = self.client.post(
            reverse('assets-api-folders'),
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_folder_read_only_fields_success(self):
        self.client.login(username='test_user', password='test')
        payload = {
            'title': 'Folder',
            'id': 10,
            'owner': 2,
        }
        response = self.client.post(
            reverse('assets-api-folders'),
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Folder.objects.filter(title='Folder').first().owner, self.test_user)
        self.assertNotEqual(Folder.objects.filter(title='Folder').first().pk, 10)

    def test_custom_permission_failed(self):
        self.client.login(username='test_user', password='test')
        payload = {
            'title': 'Folder',
            'parent': self.folder.pk

        }
        response = self.client.post(
            reverse('assets-api-folders'),
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_folder_with_file_failed(self):
        file = TemporaryFile()
        payload = {
            'title': 'Folder',
            'file': file

        }
        response = self.client.post(
            reverse('assets-api-folders'),
            payload,
            format='multipart'
        )

        file.close()

        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)


class FolderListTests(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(username='test_user',
                                                  password='test',
                                                  email='test@test.test')

        self.test_user_2 = User.objects.create_user(username='test_user_2',
                                                    password='test',
                                                    email='test_2@test.test')
        self.client = APIClient()

        self.folder = Folder.objects.create(
            title='test_folder_1',
            owner=self.test_user,
            parent=None,
        )

        self.folder = Folder.objects.create(
            title='test_folder_2',
            owner=self.test_user,
            parent=None,
        )

        self.folder = Folder.objects.create(
            title='test_folder_3',
            owner=self.test_user_2,
            parent=None,
        )

    def test_folder_list_wrong_user_login(self):
        self.client.login(username='wrong_user', password='wrong_pass')
        response = self.client.get(reverse('assets-api-folders'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_folder_list_without_login(self):
        response = self.client.get(reverse('assets-api-folders'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_folder_list_by_user(self):
        self.client.login(username='test_user', password='test')
        response = self.client.get(reverse('assets-api-folders'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue({'title': 'test_folder_1', 'parent': None} in response.json())
        self.assertTrue({'title': 'test_folder_3', 'parent': None} not in response.json())
