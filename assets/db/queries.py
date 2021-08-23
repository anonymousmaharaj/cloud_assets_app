from django.db import connection


def get_assets_list(folder_id):
    query_param = None if folder_id is None else f'{folder_id}'
    query = '''
            SELECT id, title, folder_id_id AS parent_id, False AS is_folder
            FROM assets_file
            WHERE folder_id_id = %s OR (%s IS NULL and folder_id_id IS NULL)
            UNION
            SELECT id, title, parent_id_id as parent_id, True AS is_folder
            FROM assets_folder
            WHERE parent_id_id = %s OR (%s IS NULL and parent_id_id IS NULL)'''
    with connection.cursor() as cursor:
        cursor.execute(query, [query_param, query_param, query_param, query_param])
        rows = dictfetchall(cursor)
        print(rows)
        return rows


def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
