from django.db import connection


def get_assets_list(folder_id):
    query = """
        SELECT id, title, folder_id AS parent_id, False AS is_folder
          FROM assets_file
         WHERE folder_id = :id
            OR (:id IS NULL and folder_id IS NULL)
         UNION
        SELECT id, title, parent_id AS parent_id, True AS is_folder
          FROM assets_folder
         WHERE parent_id = :id
            OR (:id IS NULL and parent_id IS NULL)"""

    with connection.cursor() as cursor:
        cursor.execute(query, {'id': folder_id})
        rows = dictfetchall(cursor)
        return rows


def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
