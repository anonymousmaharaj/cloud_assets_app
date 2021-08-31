"""Models of assets app."""

from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.urls import reverse


class File(models.Model):
    """Type of user assets.

    Related with Folder.
    """

    title = models.CharField(max_length=150)
    folder = models.ForeignKey('Folder',
                               on_delete=models.PROTECT,
                               null=True,
                               blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT)

    class Meta:
        """Metadata for File model."""

        constraints = [
            UniqueConstraint(
                name='file_title_folder_owner_key',
                fields=['title', 'folder', 'owner'],
            ),
            UniqueConstraint(
                name='file_title_owner_key',
                fields=['title', 'owner'],
                condition=Q(folder=None),
            ),
        ]

    def __str__(self):
        """Return title when called."""
        return self.title

    @staticmethod
    def create_file(title, owner, folder=None):
        """Create new object in table."""
        File.objects.create(title=title, folder=folder, owner=owner)


class Folder(models.Model):
    """Type of user assets.

    Self-linked. May contain other objects.
    """

    title = models.CharField(max_length=150)
    parent = models.ForeignKey('Folder',
                               on_delete=models.PROTECT,
                               null=True,
                               blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT)

    class Meta:
        """Metadata for Folder model."""

        constraints = [
            UniqueConstraint(
                name='folder_title_parent_owner_key',
                fields=['title', 'parent', 'owner']),

            UniqueConstraint(
                name='folder_title_owner_key',
                fields=['title', 'owner'],
                condition=Q(folder=None)
            )
        ]

    def __str__(self):
        """Return title when called."""
        return self.title

    def get_absolute_url(self):
        """Return absolute url of object."""
        return reverse('folder_page', kwargs={'folder_id': self.pk})
