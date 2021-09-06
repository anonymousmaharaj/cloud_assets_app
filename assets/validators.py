"""Any validators for Assets app."""

import os.path

from assets import models


def validate_upload_file(file_path):
    """Validate file path for exist."""
    return os.path.exists(file_path) and os.path.isfile(file_path)


def validate_exist_file_in_folder(file_path, user, folder=None):
    """Validate exists file in DB in folder."""
    file_exist = models.File.objects.filter(title=os.path.basename(file_path),
                                            owner=user,
                                            folder=folder)
    return len(file_exist) > 0


def validate_exist_file(user, file_id):
    """Validate exists file in DB."""
    file_exist = models.File.objects.filter(pk=file_id,
                                            owner=user)
    return len(file_exist) > 0


# TODO: Fix both responses below
def validate_folder_id(folder_id):
    """Validate value of 'folder' param."""
    if folder_id is not None:
        return True if folder_id.isdigit() else False
    return True


def validate_file_id(file_id):
    """Validate value of 'file' param."""
    if file_id is not None:
        return True if file_id.isdigit() else False
    return False


def validate_get_params(params):
    """Validate get parameters."""
    accept_params = ['folder', 'file']
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


def validate_permission(user, file_id):
    """Validate exists file in DB."""
    file_obj = models.File.objects.filter(pk=file_id)
    if len(file_obj) > 0:
        return True if file_obj[0].owner == user else False
    return False


def validate_exist_folder(parent_folder):
    if parent_folder is not None:
        folders_list = models.Folder.objects.filter(pk=parent_folder)
        return len(folders_list) > 0
    else:
        return True
