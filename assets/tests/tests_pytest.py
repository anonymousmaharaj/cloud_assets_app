"""Tests with pytest."""

from tempfile import TemporaryFile

import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse

from assets import models
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient


@pytest.fixture
def create_users():
    User = get_user_model()

    test_user = User.objects.create_user(username='test_user',
                                         password='test',
                                         email='test@test.test')

    test_user_2 = User.objects.create_user(username='test_user_2',
                                           password='test',
                                           email='test_2@test.test')
    return [test_user, test_user_2]


@pytest.fixture
def create_folder(create_users):
    models.Folder.objects.create(
        title='test_folder_1',
        owner=create_users[1],
        parent=None,
    )


@pytest.mark.django_db
def test_create_folder_success(api_client, create_users):
    users = create_users

    client = api_client()
    client.force_login(users[0])

    payload = {
        'title': '<script>XSS Attack</script>',
    }

    response = client.post(
        reverse('assets-api-folders'),
        payload,
        format='json'
    )
    assert response.status_code == 201
    assert response.data['title'] == 'XSS Attack'
    assert models.Folder.objects.count() == 1
    assert models.Folder.objects.filter(title='XSS Attack').first().owner == users[0]


@pytest.mark.django_db
def test_create_folder_failed(api_client):
    client = api_client()

    payload = {
        'title': '<script>XSS Attack</script>',
    }
    response = client.post(
        reverse('assets-api-folders'),
        payload,
        format='json'
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_create_folder_wrong_field_failed(api_client, create_users):
    users = create_users

    client = api_client()
    client.force_login(users[0])

    payload = {
        'wrong_title': '<script>XSS Attack</script>',
    }

    response = client.post(
        reverse('assets-api-folders'),
        payload,
        format='json'
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_folder_read_only_fields_success(api_client, create_users):
    users = create_users

    client = api_client()
    client.force_login(users[0])

    payload = {
        'title': 'Folder',
        'id': 10,
        'owner': 2,
    }
    response = client.post(
        reverse('assets-api-folders'),
        payload,
        format='json'
    )

    assert response.status_code == 201
    assert models.Folder.objects.filter(title='Folder').first().owner == users[0]
    assert models.Folder.objects.filter(title='Folder').first().pk != 10


@pytest.mark.django_db
def test_custom_permission_failed(api_client, create_users, create_folder):
    users = create_users

    client = api_client()
    client.force_login(users[0])

    payload = {
        'title': 'Folder',
        'parent': models.Folder.objects.get(pk=1).pk

    }
    response = client.post(
        reverse('assets-api-folders'),
        payload,
        format='json'
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_custom_permission_failed(api_client, create_users):
    users = create_users

    client = api_client()
    client.force_login(users[0])

    file = TemporaryFile()

    payload = {
        'title': 'Folder',
        'file': file

    }

    response = client.post(
        reverse('assets-api-folders'),
        payload,
        format='multipart'
    )

    assert response.status_code == 415
