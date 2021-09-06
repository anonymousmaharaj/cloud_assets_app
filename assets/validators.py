"""Any validators for Assets app."""

import os.path

from assets import models


def validate_upload_file(file_path):
    """Validate file path for exist."""
    return os.path.exists(file_path) and os.path.isfile(file_path)


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
            return False
    return True


def validate_get_params(params):
    """Validate get parameters."""
    accept_params = ['folder']
    for param in params:
        if param not in accept_params:
            return False
    return True


def validate_id_for_folder(folder_id):
    """Validate value of 'folder' param.

    Using for create new folder and upload file in to.
    """
    if folder_id is None:
        return True
    elif folder_id.isdigit():
        return True
    else:
        return False


def validate_new_folder_name(folder_name):
    """Validate folder's name."""
    return False if len(folder_name) > 255 else True
