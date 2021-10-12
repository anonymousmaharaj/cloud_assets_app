"""All custom permissions."""
from rest_framework import permissions

from assets import models


class IsFolderOwner(permissions.BasePermission):
    """Permission to check if a parent folder is owned by a user."""

    def has_permission(self, request, view):
        """Permission to check if a parent folder is owned by a user."""
        if request.data.get('folder') is None:
            return True
        return request.user.folders.filter(pk=request.data.get('folder')).exists()


class IsParentOwner(permissions.BasePermission):
    """Permission to check if a parent folder is owned by a user."""

    def has_permission(self, request, view):
        """Permission to check if a parent folder is owned by a user."""
        if request.data.get('parent') is None:
            return True
        return request.user.folders.filter(pk=request.data.get('parent')).exists()


class IsObjectOwner(permissions.BasePermission):
    """Permission to check if a folder is owned by a user."""

    def has_object_permission(self, request, view, obj):
        """Check if a object is owned by a user."""
        return obj.owner == request.user


class IsShareOwner(permissions.BasePermission):
    """Permission to check if a share is owned by a user."""

    def has_object_permission(self, request, view, obj):
        """Check if a share is owned by a user."""
        return obj in models.SharedTable.objects.filter(
            file_id__in=[file.id for file in request.user.files.all()])


class IsSharingFileOwner(permissions.BasePermission):
    """Permission to check if a sharing file is owned by a user."""

    def has_permission(self, request, view):
        if request.data.get('file') is None:
            return True
        return request.data.get('file') in [file.pk for file in request.user.files.all()]
