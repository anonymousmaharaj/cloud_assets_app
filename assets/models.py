from django.db import models
from django.urls import reverse


# Create your models here.
class File(models.Model):
    title = models.CharField(max_length=150)
    folder_id = models.ForeignKey('Folder',
                                  on_delete=models.CASCADE,
                                  null=True,
                                  blank=True)

    def __str__(self):
        return self.title


class Folder(models.Model):
    title = models.CharField(max_length=150)
    parent_id = models.ForeignKey('Folder',
                                  on_delete=models.CASCADE,
                                  null=True,
                                  blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('folder_page', kwargs={'folder_id': self.pk})
