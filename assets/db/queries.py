"""Queries and related objects."""

from django.db import connection

from assets import models


def get_assets_list(folder_id, user_pk):
    """Raw SQL query for receiving assets of folder or a root page."""
    query = """
        SELECT id, title, folder_id AS parent_id, False AS is_folder
          FROM assets_file
         WHERE (folder_id = %(folder_id)s
            OR (%(folder_id)s IS NULL and folder_id IS NULL))
           AND owner_id = %(owner)s
         UNION
        SELECT id, title, parent_id AS parent_id, True AS is_folder
          FROM assets_folder
         WHERE (parent_id = %(folder_id)s
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


def move_file(new_folder_id, file_id):
    """Move file in DB."""
    file = models.File.objects.get(pk=file_id)
    file.folder_id = new_folder_id
    file.save()


def rename_file(file_id, new_title):
    """Rename file in DB."""
    file = models.File.objects.get(pk=file_id)
    file.title = new_title
    file.save()
