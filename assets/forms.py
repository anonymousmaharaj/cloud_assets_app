"""Forms for Assets application."""
import bleach
from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from assets import models


class RenameFolderForm(forms.ModelForm):
    """Form for rename folder."""

    class Meta:
        model = models.Folder
        fields = ['title']

    def clean_title(self):
        """Clean title field from any HTML tags."""
        return bleach.clean(self.cleaned_data['title'], tags=[], strip=True, strip_comments=True)


class UpdateShareForm(forms.ModelForm):
    """"""
    expired = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M:%S'])
    permissions = forms.ModelMultipleChoiceField(queryset=models.Permissions.objects.all(),
                                                 widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = models.SharedTable
        fields = ['expired', 'permissions']

    def clean_expired(self):
        if self.cleaned_data['expired'] < timezone.now():
            raise forms.ValidationError('Cannot be less then now.')

        return self.cleaned_data['expired']


class CreateShareForm(forms.Form):

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    email = forms.EmailField()
    expired = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M'],
                                  widget=forms.DateTimeInput(attrs={'placeholder': 'year-m-d hours:min'}))
    permissions = forms.ModelMultipleChoiceField(queryset=models.Permissions.objects.all(),
                                                 widget=forms.CheckboxSelectMultiple)

    def clean_email(self):
        if self.cleaned_data['email'] == self.user.email:
            raise forms.ValidationError('Cannot share with yourself.')

        if not User.objects.filter(email=self.cleaned_data['email']).exists():
            raise forms.ValidationError('User with this email does not exist')

        return self.cleaned_data['email']

    def clean_expired(self):
        if self.cleaned_data['expired'] < timezone.now():
            raise forms.ValidationError('Cannot be less then now.')

        return self.cleaned_data['expired']


class RenameFileForm(forms.Form):
    """Form for rename file."""

    new_title = forms.CharField(label='new_title', max_length=255)

    def clean_new_title(self):
        """Clean new_title field from any HTML tags."""
        return bleach.clean(self.cleaned_data['new_title'], tags=[], strip=True, strip_comments=True)


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
