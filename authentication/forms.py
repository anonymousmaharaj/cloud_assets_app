"""Forms for auth app."""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


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
