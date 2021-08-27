from django import forms
from django.contrib.auth.forms import AuthenticationForm


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Username')
    password = forms.CharField(label='Password')


"""Customs forms for Assets app."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class UserRegisterForm(UserCreationForm):
    """Custom form for registration."""

    email = forms.EmailField()

    class Meta:
        """Init Meta class for UserCreationForm."""

        model = User
        fields = ('username', 'email', 'password1', 'password2')
