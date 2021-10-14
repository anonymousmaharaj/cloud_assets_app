from tempfile import TemporaryFile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from assets.models import Folder, File, Permissions, SharedTable


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
        self.client.login(username='test_user', password='test')
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

        self.folder_1 = Folder.objects.create(
            title='test_folder_1',
            owner=self.test_user,
            parent=None,
        )

        self.folder_2 = Folder.objects.create(
            title='test_folder_2',
            owner=self.test_user,
            parent=None,
        )

        self.folder_3 = Folder.objects.create(
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


class ShareListTests(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(username='test_user',
                                                  password='test',
                                                  email='test@test.test')

        self.test_user_2 = User.objects.create_user(username='test_user_2',
                                                    password='test',
                                                    email='test_2@test.test')
        self.client = APIClient()

        self.file_1 = File.objects.create(
            title='test_file_1',
            owner=self.test_user,
            folder=None,
            extension='.txt',
            size=1024
        )

        self.file_2 = File.objects.create(
            title='test_file_2',
            owner=self.test_user,
            folder=None,
            extension='.txt',
            size=1024

        )

        self.file_3 = File.objects.create(
            title='test_file_3',
            owner=self.test_user_2,
            folder=None,
            extension='.txt',
            size=1024
        )

        self.perm_read = Permissions.objects.create(
            title='Download',
            name='read_only'
        )

        self.perm_rename = Permissions.objects.create(
            title='Rename',
            name='rename_only'
        )
        self.perm_delete = Permissions.objects.create(
            title='Delete',
            name='delete_only'
        )

        self.shared_table = SharedTable.objects.create(
            file=self.file_1,
            user=self.test_user_2,
            expired='2022-01-22 10:05',
        )
        self.shared_table.permissions.set([self.perm_read, self.perm_rename])

    def test_share_list_count(self):
        self.client.login(username='test_user', password='test')
        response = self.client.get(reverse('assets-share-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(len(response.data[0]['permissions']), 2)

    def test_share_list_count_empty(self):
        self.client.login(username='test_user_2', password='test')
        response = self.client.get(reverse('assets-share-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_share_list_count_auth_error(self):
        self.client.login(username='wrong_test_user', password='test')
        response = self.client.get(reverse('assets-share-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_share_list_count_empty_auth(self):
        response = self.client.get(reverse('assets-share-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ShareCreateTests(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(username='test_user',
                                                  password='test',
                                                  email='test@test.test')

        self.test_user_2 = User.objects.create_user(username='test_user_2',
                                                    password='test',
                                                    email='test_2@test.test')
        self.client = APIClient()

        self.file_1 = File.objects.create(
            title='test_file_1',
            owner=self.test_user,
            folder=None,
            extension='.txt',
            size=1024
        )

        self.file_2 = File.objects.create(
            title='test_file_2',
            owner=self.test_user,
            folder=None,
            extension='.txt',
            size=1024
        )

        self.file_3 = File.objects.create(
            title='test_file_3',
            owner=self.test_user_2,
            folder=None,
            extension='.txt',
            size=1024
        )

        self.perm_read = Permissions.objects.create(
            title='Download',
            name='read_only'
        )

        self.perm_rename = Permissions.objects.create(
            title='Rename',
            name='rename_only'
        )
        self.perm_delete = Permissions.objects.create(
            title='Delete',
            name='delete_only'
        )

    def test_create_share_correct_user(self):
        self.client.force_authenticate(user=self.test_user)
        payload = {
            'file': self.file_1.pk,
            'email': 'test_2@test.test',
            'permissions': [self.perm_rename.pk, self.perm_read.pk],
            'expired': '2022-01-22 10:05'
        }
        response = self.client.post(
            reverse('assets-share-list'),
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SharedTable.objects.count(), 1)
        self.assertEqual(SharedTable.objects.filter(user=self.test_user_2).first().file_id, self.file_1.pk)

    def test_create_share_file_incorrect_user(self):
        self.client.login(username='test_user', password='test')
        payload = {
            'file': self.file_3.pk,
            'email': 'test_2@test.test',
            'permissions': [self.perm_rename.pk, self.perm_read.pk],
            'expired': '2022-01-22 10:05'
        }
        response = self.client.post(reverse('assets-share-list'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SharedTable.objects.count(), 0)

    def test_create_share_exist(self):
        self.client.login(username='test_user', password='test')
        payload = {
            'file': self.file_1.pk,
            'email': 'test_2@test.test',
            'permissions': [self.perm_rename.pk, self.perm_read.pk],
            'expired': '2022-01-22 10:05'
        }
        self.client.post(reverse('assets-share-list'), payload, format='json')
        response = self.client.post(reverse('assets-share-list'), payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_share_wrong_fields(self):
        self.client.login(username='test_user', password='test')
        payload = {
            'file_wrong_field': self.file_1.pk,
            'email_wrong_field': 'test_2@test.test',
            'permissions': [self.perm_rename.pk, self.perm_read.pk],
            'expired': '2022-01-22 10:05'
        }
        response = self.client.post(
            reverse('assets-share-list'),
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SharedTable.objects.count(), 0)

    def test_create_share_file_not_found(self):
        self.client.login(username='test_user', password='test')
        payload = {
            'file': 10,
            'email': 'test_2@test.test',
            'permissions': [self.perm_rename.pk, self.perm_read.pk],
            'expired': '2022-01-22 10:05'
        }
        response = self.client.post(
            reverse('assets-share-list'),
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SharedTable.objects.count(), 0)


class ShareUpdateDestroyTests(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(username='test_user',
                                                  password='test',
                                                  email='test@test.test')

        self.test_user_2 = User.objects.create_user(username='test_user_2',
                                                    password='test',
                                                    email='test_2@test.test')
        self.client = APIClient()

        self.file_1 = File.objects.create(
            title='test_file_1',
            owner=self.test_user,
            folder=None,
            extension='.txt',
            size=1024
        )

        self.file_2 = File.objects.create(
            title='test_file_2',
            owner=self.test_user,
            folder=None,
            extension='.txt',
            size=1024
        )

        self.file_3 = File.objects.create(
            title='test_file_3',
            owner=self.test_user_2,
            folder=None,
            extension='.txt',
            size=1024
        )

        self.perm_read = Permissions.objects.create(
            title='Download',
            name='read_only'
        )

        self.perm_rename = Permissions.objects.create(
            title='Rename',
            name='rename_only'
        )

        self.perm_delete = Permissions.objects.create(
            title='Delete',
            name='delete_only'
        )

        self.shared_table = SharedTable.objects.create(
            file=self.file_1,
            user=self.test_user_2,
            expired='2022-01-22 10:05',
        )
        self.shared_table.permissions.set([self.perm_read, self.perm_rename])

        self.shared_table_2 = SharedTable.objects.create(
            file=self.file_3,
            user=self.test_user,
            expired='2022-01-22 10:05',
        )
        self.shared_table.permissions.set([self.perm_read, self.perm_rename])

    def test_update_share_correct_user(self):
        self.client.force_authenticate(user=self.test_user)

        payload = {
            'permissions': [self.perm_rename.pk],
            'expired': '2022-02-22 10:05'
        }
        response = self.client.put(
            f'/api/assets/files/shared/{self.shared_table.pk}/',
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.shared_table.user.pk)
        self.assertEqual(len(response.data['permissions']), 1)

    def test_update_share_wrong_fields(self):
        self.client.login(username='test_user', password='test')

        payload = {
            'id': 4,
            'user': 1
        }
        response = self.client.put(
            f'/api/assets/files/shared/{self.shared_table.pk}/',
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_share_incorrect_user(self):
        self.client.login(username='test_user', password='test')

        payload = {
            'permissions': [self.perm_rename.pk],
            'expired': '2022-02-22 10:05'
        }
        response = self.client.put(
            f'/api/assets/files/share/{self.shared_table_2.pk}/',
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_share_correct_user(self):
        self.client.login(username='test_user', password='test')
        response = self.client.delete(f'/api/assets/files/shared/{self.shared_table.pk}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_share_incorrect_user(self):
        self.client.login(username='test_user_2', password='test')
        response = self.client.delete(f'/api/assets/files/shared/{self.shared_table.pk}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ShareFileRetrieveUpdateDestroyTests(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(username='test_user',
                                                  password='test',
                                                  email='test@test.test')

        self.test_user_2 = User.objects.create_user(username='test_user_2',
                                                    password='test',
                                                    email='test_2@test.test')
        self.client = APIClient()

        self.file_1 = File.objects.create(
            title='test_file_1',
            owner=self.test_user,
            folder=None,
            extension='.txt',
            size=1024
        )

        self.file_2 = File.objects.create(
            title='test_file_2',
            owner=self.test_user,
            folder=None,
            extension='.txt',
            size=1024
        )

        self.perm_rename = Permissions.objects.create(
            title='Rename',
            name='rename_only'
        )

        self.perm_delete = Permissions.objects.create(
            title='Delete',
            name='delete_only'
        )

        self.shared_table = SharedTable.objects.create(
            file=self.file_1,
            user=self.test_user_2,
            expired='2022-01-22 10:05',
        )
        self.shared_table.permissions.set([self.perm_delete])

        self.shared_table_2 = SharedTable.objects.create(
            file=self.file_2,
            user=self.test_user_2,
            expired='2022-01-22 10:05',
        )
        self.shared_table_2.permissions.set([self.perm_rename])

    def test_update_file_correct(self):
        self.client.force_authenticate(user=self.test_user_2)
        payload = {
            'title': '<script>newtitle</script>',
        }
        response = self.client.put(
            f'/api/assets/files/shared-with-me/{self.file_2.pk}/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'newtitle')

    def test_update_file_no_update_permissions(self):
        self.client.force_authenticate(user=self.test_user_2)
        payload = {
            'title': '<script>newtitle</script>',
        }
        response = self.client.put(
            f'/api/assets/files/shared-with-me/{self.file_1.pk}/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_file_wrong_user(self):
        self.client.force_authenticate(user=self.test_user)
        payload = {
            'title': '<script>newtitle</script>',
        }
        response = self.client.put(
            f'/api/assets/files/shared-with-me/{self.file_2.pk}/',
            payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_file_wrong_fields(self):
        self.client.force_authenticate(user=self.test_user_2)
        response = self.client.put(
            f'/api/assets/files/shared-with-me/{self.file_2.pk}/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_file_correct(self):
        self.client.force_authenticate(user=self.test_user_2)
        response = self.client.delete(f'/api/assets/files/shared-with-me/{self.file_1.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_file_wrong_user(self):
        self.client.force_authenticate(user=self.test_user)
        response = self.client.delete(f'/api/assets/files/shared-with-me/{self.file_1.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_file_no_delete_permissions(self):
        self.client.force_authenticate(user=self.test_user)
        response = self.client.delete(f'/api/assets/files/shared-with-me/{self.file_1.pk}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ThumbnailCreateTest(APITestCase):

    def setUp(self):
        self.test_user = User.objects.create_user(username='test_user',
                                                  password='test',
                                                  email='test@test.test')

        self.client = APIClient()

        self.file_1 = File.objects.create(
            title='test_file_1',
            owner=self.test_user,
            folder=None,
            extension='.txt',
            size=1024,
            relative_key=f'users/{self.test_user.pk}/assets/12345678'
        )

    @patch('assets.aws.s3.check_exists')
    def test_create_thumbnail_success(self, patch_api):
        patch_api.return_value = True
        self.client.force_authenticate(user=self.test_user)
        payload = {
            'thumbnail_key': f'thumbnails/{self.file_1.relative_key}',
        }
        response = self.client.post(
            f'/api/assets/files/thumbnail/12345678/',
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('assets.aws.s3.check_exists')
    def test_create_thumbnail_wrong_field(self, patch_api):
        patch_api.return_value = True
        self.client.force_authenticate(user=self.test_user)
        payload = {
            'thumbnail_keys': f'thumbnails/{self.file_1.relative_key}',
        }
        response = self.client.post(
            f'/api/assets/files/thumbnail/12345678/',
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_thumbnail_great_then_255(self):
        self.client.force_authenticate(user=self.test_user)
        payload = {
            'thumbnail_key': str(''.join(str(x) for x in range(400))),
        }
        response = self.client.post(
            f'/api/assets/files/thumbnail/12345678/',
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_thumbnail_wrong(self):
        self.client.force_authenticate(user=self.test_user)
        payload = {
            'thumbnail_key': f'thumbnails/{self.file_1.relative_key}',
        }
        response = self.client.post(
            f'/api/assets/files/thumbnail/12345678/',
            payload,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
