"""Module containing auxiliary functions."""

import io

import xlsxwriter

from celery_settings import celery_app
from s3 import upload_excel_to_bucket


@celery_app.task
def create_excel_file(rows: list, user_id: int) -> None:
    """
    Generate excel file and call upload_excel_to_bucket() to upload it.

    Args:
        rows: List of tuples containing file's extension and counts.
        user_id: User's identifier from database to send it to upload_excel_to_bucket() function.
    """
    with io.BytesIO() as output_file:
        workbook = xlsxwriter.Workbook(output_file, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        for index, values in enumerate(rows):
            worksheet.write_row(row=index, col=0, data=values)

        workbook.close()
        output_file.seek(0)
        upload_excel_to_bucket(output_file, user_id)
