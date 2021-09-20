"""All custom permissions."""

from rest_framework import permissions


class IsFolderOwner(permissions.BasePermission):
    """Permission to check if a folder is owned by a user."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
