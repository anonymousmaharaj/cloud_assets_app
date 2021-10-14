"""Forms for auth app."""
import os

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class UserLoginForm(AuthenticationForm):
    """Basic class for login."""

    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserRegisterForm(UserCreationForm):
    """Custom form for registration."""

    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    invite_code = forms.CharField(max_length=30, label='Invite code',
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        """Init Meta class for UserCreationForm."""

        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_invite_code(self):
        if self.cleaned_data['invite_code'] != os.getenv('INVITE_CODE'):
            raise forms.ValidationError('Enter a valid invite code')
