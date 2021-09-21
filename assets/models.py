"""Models of assets app."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse


class File(models.Model):
    """Type of user assets.

    Related with Folder.
    """

    title = models.CharField(max_length=255)
    folder = models.ForeignKey('Folder',
                               on_delete=models.PROTECT,
                               null=True,
                               blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT)
    relative_key = models.CharField(max_length=255)

    class Meta:
        """Metadata for File model."""

        constraints = [
            models.UniqueConstraint(
                name='assets_file_title_folder_owner_key',
                fields=['title', 'folder', 'owner'],
            ),
            models.UniqueConstraint(
                name='assets_file_title_owner_key',
                fields=['title', 'owner'],
                condition=Q(folder=None),
            ),
        ]

    def __str__(self):
        """Return title when called."""
        return self.title

    def clean(self):
        """Check exist file with same title."""
        if File.objects.filter(title=self.title, owner=self.owner, folder=self.folder).first():
            raise ValidationError('Current file already exists.')


class Folder(models.Model):
    """Type of user assets.

    Self-linked. May contain other objects.
    """

    title = models.CharField(max_length=255)
    parent = models.ForeignKey('Folder',
                               on_delete=models.PROTECT,
                               null=True,
                               blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT,
                              related_name='folders')

    class Meta:
        """Metadata for Folder model."""

        constraints = [
            models.UniqueConstraint(
                name='assets_folder_title_parent_owner_key',
                fields=['title', 'parent', 'owner'],
            ),
            models.UniqueConstraint(
                name='assets_folder_title_owner_key',
                fields=['title', 'owner'],
                condition=Q(parent=None)
            )
        ]

    def __str__(self):
        """Return title when called."""
        return self.title

    def get_absolute_url(self):
        """Return absolute url of object."""
        return reverse('folder_page', kwargs={'folder_id': self.pk})

    def clean(self):
        """Check exist folder with same title."""
        if Folder.objects.filter(title=self.title, owner=self.owner, parent=self.parent).first():
            raise ValidationError('Current folder already exists.')
        if self == self.parent:
            raise ValidationError('Cannot move folder in itself.')
