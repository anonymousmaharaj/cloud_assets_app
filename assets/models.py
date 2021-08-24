from django.db import models
from django.urls import reverse


class File(models.Model):
    title = models.CharField(max_length=150)
    folder = models.ForeignKey('Folder',
                               on_delete=models.PROTECT,
                               null=True,
                               blank=True)

    def __str__(self):
        return self.title


class Folder(models.Model):
    title = models.CharField(max_length=150)
    parent = models.ForeignKey('Folder',
                               on_delete=models.PROTECT,
                               null=True,
                               blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('folder_page', kwargs={'folder_id': self.pk})
