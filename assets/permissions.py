"""All custom permissions."""
from rest_framework import permissions


class IsObjectOwner(permissions.BasePermission):
    """Permission to check if a folder is owned by a user."""

    def has_object_permission(self, request, view, obj):
        """Check if a object is owned by a user."""
        return obj.owner == request.user

