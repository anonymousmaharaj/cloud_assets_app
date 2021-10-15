"""Queries and related objects."""

from django.db import connection
from django.utils import timezone

from assets import models


def get_assets_list(folder_id, user_pk):
    """Raw SQL query for receiving assets of folder or a root page."""
    query = """
        SELECT id, title, folder_id AS parent_id, False AS is_folder, SPLIT_PART(relative_key, '/', 4)::text as uuid
          FROM assets_file
         WHERE (folder_id = (select id
                   from assets_folder
                   where uuid::text = %(folder_id)s)
            OR (%(folder_id)s IS NULL and folder_id IS NULL))
           AND owner_id = %(owner)s
         UNION
        SELECT id, title, parent_id AS parent_id, True AS is_folder, uuid::text as uuid
          FROM assets_folder
         WHERE (parent_id = (select id
                   from assets_folder
                   where uuid::text = %(folder_id)s)
            OR (%(folder_id)s IS NULL and parent_id IS NULL))
            AND owner_id = %(owner)s
      ORDER BY is_folder DESC"""

    with connection.cursor() as cursor:
        cursor.execute(query, {'folder_id': folder_id, 'owner': user_pk})
        rows = dictfetchall(cursor)
        return rows


def dictfetchall(cursor):
    """Return all rows from a cursor as a dict."""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def delete_recursive(folder_id):
    """Recursive deleting folders and files."""
    folders = models.Folder.objects.filter(parent=folder_id)
    models.File.objects.filter(folder=folder_id).delete()
    if len(folders) > 0:
        for folder in folders:
            delete_recursive(folder.pk)
    models.Folder.objects.filter(pk=folder_id).delete()


def get_personal_folders(user):
    """Return all folders in form."""
    return models.Folder.objects.filter(owner=user)


def move_file(new_folder, uuid):
    """Move file in DB."""
    file = models.File.objects.filter(relative_key__contains=uuid).first()
    file.folder = new_folder
    file.save()


def rename_file(uuid, new_title):
    """Rename file in DB."""
    file = models.File.objects.filter(relative_key__contains=uuid).first()
    file.title = new_title
    file.save()


def rename_folder(folder_id, new_title):
    """Rename folder in DB."""
    folder_obj = models.Folder.objects.get(pk=folder_id)
    folder_obj.title = new_title
    folder_obj.save()


def create_file(file_name, user, folder, key, size, extension):
    """Create file in DB."""
    models.File(title=file_name,
                owner=user,
                folder=folder,
                relative_key=key,
                size=size,
                extension=extension).save()


def delete_file(uuid):
    """Delete file form DB."""
    models.File.objects.filter(relative_key__contains=uuid).delete()


def create_folder(user, title, parent):
    """Create new folder in DB."""
    models.Folder.objects.create(title=title,
                                 owner=user,
                                 parent=parent).save()


def delete_shared_table(uuid):
    """Delete share table."""
    models.SharedTable.objects.filter(file__relative_key__contains=uuid).delete()


def delete_expired_shares():
    now = timezone.now()
    models.SharedTable.objects.filter(expired__lt=now).delete()
