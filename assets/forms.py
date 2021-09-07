"""Forms for Assets application."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from assets import models


class RenameFileForm(forms.Form):
    """Form for rename file."""

    new_title = forms.CharField(label='new_title')


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

    path = forms.CharField(label='path')


class CreateFolderForm(forms.Form):
    """Form for create new folder."""

    title = forms.CharField(label='title', max_length=255)


class UserLoginForm(AuthenticationForm):
    """Basic class for login."""

    username = forms.CharField(label='Username')
    password = forms.PasswordInput()


class UserRegisterForm(UserCreationForm):
    """Custom form for registration."""

    email = forms.EmailField()

    class Meta:
        """Init Meta class for UserCreationForm."""

        model = User
        fields = ('username', 'email', 'password1', 'password2')
