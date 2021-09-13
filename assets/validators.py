"""Any validators for Assets app."""

from assets import models


def validate_exist_file_in_folder(file_name, user, folder=None):
    """Validate exists file in DB in folder."""
    file_exist = models.File.objects.filter(title=file_name,
                                            owner=user,
                                            folder=folder).exists()
    return file_exist


def validate_exist_file(user, file_id):
    """Validate exists file in DB."""
    file_exist = models.File.objects.filter(pk=file_id,
                                            owner=user).exists()
    return file_exist


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


def validate_new_name(folder_name):
    """Validate folder's name."""
    return False if len(folder_name) > 255 else True


def validate_file_permission(user, file_id):
    """Validate permissions for the file."""
    file_obj = models.File.objects.filter(pk=file_id).exists()
    if file_obj:
        file_obj = models.File.objects.get(pk=file_id)
        return True if file_obj.owner == user else False
    return False


def validate_folder_permission(user, folder_id):
    """Validate permissions for the folder."""
    folder_obj = models.Folder.objects.filter(pk=folder_id).exists()
    if folder_obj:
        folder_obj = models.Folder.objects.get(pk=folder_id)
        return True if folder_obj.owner == user else False
    return False


def validate_parent_folder(parent_folder):
    """Validate parents folder exist."""
    if parent_folder is not None:
        folders_list = models.Folder.objects.filter(pk=parent_folder).exists()
        return folders_list
    else:
        return True


def validate_exist_parent_folder(parent_folder, title, user):
    """Validate parents folder exist."""
    folders_list = models.Folder.objects.filter(
        parent=parent_folder,
        owner=user,
        title=title).exists()
    return folders_list


def validate_exist_folder_new_title(folder_id, new_title, user):
    """Validate new folder's title for rename."""
    folder_obj = models.Folder.objects.filter(pk=folder_id).exists()
    if not folder_obj:
        return False
    parent_folder_obj = models.Folder.objects.get(pk=folder_id)
    folders_list = models.Folder.objects.filter(parent=parent_folder_obj.parent,
                                                owner=user,
                                                title=new_title).exists()
    return folders_list


def validate_exist_current_folder(folder_id):
    """Validate folder's exist."""
    folders_list = models.Folder.objects.filter(pk=folder_id).exists()
    return folders_list
