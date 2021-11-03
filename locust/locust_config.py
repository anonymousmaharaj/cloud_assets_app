"""Module for configure Locust."""

import os
import string
import random

from locust import HttpUser, task, between
from requests.auth import HTTPBasicAuth


def get_random_title() -> str:
    """
    Generate and return random string title.
    Returns:
        (str): Generated title.
    """
    return ''.join(random.choice(string.ascii_letters) for i in range(10))


class APIUserBehavior(HttpUser):
    """Class description tasks for performance testing via api endpoints."""

    def on_start(self) -> None:
        """Logging before tasks will run."""
        self.client.auth = HTTPBasicAuth(os.getenv('BASIC_LOGIN'), os.getenv('BASIC_PASSWORD'))

    @task
    def view_files(self):
        """Testing list files via api endpoint."""
        self.client.get('/api/assets/files/')

    @task
    def view_folders(self):
        """Testing list folders via api endpoint."""
        self.client.get('/api/assets/folders/')

    @task
    def create_folder(self):
        """Testing creating folders via api endpoint."""
        self.client.post('/api/assets/folders/', json={'title': get_random_title()})

    @task
    def create_file_api(self):
        """Testing creating files via api endpoint."""
        self.client.post('/api/assets/files/', json={'title': get_random_title(),
                                                     'size': 100})


class UserBehavior(HttpUser):
    """Class description tasks for performance testing via user interface."""

    wait_time = between(1, 5)

    def on_start(self) -> None:
        """Logging before tasks will run."""
        response = self.client.get('/login/')
        csrftoken = response.cookies['csrftoken']
        self.client.post('/login/',
                         {'username': os.getenv('BASIC_LOGIN'),
                          'password': os.getenv('BASIC_PASSWORD')},
                         headers={'X-CSRFToken': csrftoken})

    @task
    def create_folder(self) -> None:
        """Testing creating folders via frontend."""
        response = self.client.get('/create-folder/')
        csrf_token = response.cookies['csrftoken']
        self.client.post('/create-folder/',
                         data={'title': get_random_title()},
                         headers={"X-CSRFToken": csrf_token})
