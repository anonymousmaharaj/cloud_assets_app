"""Any validators for Assets app."""

import os.path


def validate_upload_file(file_path):
    """Validate file path for exist."""
    return True if os.path.exists(file_path) else False
