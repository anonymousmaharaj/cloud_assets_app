"""Validators for queries ana parameters."""

from django.http import HttpResponseBadRequest


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
