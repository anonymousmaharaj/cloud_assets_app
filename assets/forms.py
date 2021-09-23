"""Forms for Assets application."""

import bleach
from django import forms

from assets import models


class RenameFolderForm(forms.ModelForm):
    """Form for rename folder."""

    class Meta:
        model = models.Folder
        fields = ['title']

    def clean_title(self):
        """Clean title field from any HTML tags."""
        return bleach.clean(self.cleaned_data['title'], tags=[], strip=True, strip_comments=True)


class RenameFileForm(forms.Form):
    """Form for rename file."""

    new_title = forms.CharField(label='new_title', max_length=255)


class MoveFileForm(forms.Form):
    """Form to move file."""

    new_folder = forms.ChoiceField(widget=forms.Select,
                                   label='Move to...')

    def __init__(self, *args, **kwargs):
        """Set choices values for 'new_folder' field."""
        user = kwargs.pop('user')
        super(MoveFileForm, self).__init__(*args, **kwargs)
        folders = models.Folder.objects.filter(owner=user)
        folders = [(str(i.pk), i.title) for i in folders]
        folders.append(('None', 'Root'))
        self.fields['new_folder'].choices = folders


class UploadFileForm(forms.Form):
    """Form for input file's path."""

    file = forms.FileField()


class CreateFolderForm(forms.Form):
    """Form for create new folder."""

    title = forms.CharField(label='title', max_length=255)
