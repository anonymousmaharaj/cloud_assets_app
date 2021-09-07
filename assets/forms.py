"""Forms for Assets application."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


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
