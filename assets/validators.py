"""Any validators for Assets app."""

import os.path

from django.http import HttpResponseBadRequest

from assets import models


def validate_upload_file(file_path):
    """Validate file path for exist."""
    return os.path.exists(file_path)


def validate_exist_file(file_path, user, folder=None):
    """Validate exists file in DB."""
    file_exist = models.File.objects.filter(title=os.path.basename(file_path),
                                            owner=user,
                                            folder=folder)
    return len(file_exist) > 0


# TODO: Fix both responses below
def validate_folder_id(folder_id):
    """Validate value of 'folder' param."""
    if folder_id is not None:
        if not folder_id.isdigit():
            return HttpResponseBadRequest
    return 200


def validate_get_params(params):
    """Validate get parameters."""
    accept_params = ['folder']
    for param in params:
        if param not in accept_params:
            return HttpResponseBadRequest
    return 200
