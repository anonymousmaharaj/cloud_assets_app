"""All custom permissions."""

from rest_framework import permissions


class IsFolderOwner(permissions.BasePermission):
    """Permission to check if a parent folder is owned by a user."""

    def has_permission(self, request, view):
        if request.data.get('folder') is None:
            return True
        return request.user.folders.filter(pk=request.data.get('folder')).exists()


class IsParentOwner(permissions.BasePermission):
    """Permission to check if a parent folder is owned by a user."""

    def has_permission(self, request, view):
        if request.data.get('parent') is None:
            return True
        return request.user.folders.filter(pk=request.data.get('parent')).exists()


class IsObjectOwner(permissions.BasePermission):
    """Permission to check if a folder is owned by a user."""

    def has_object_permission(self, request, view, obj):
        """Check if a object is owned by a user."""
        return obj.owner == request.user
