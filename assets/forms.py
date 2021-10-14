"""Forms for Assets application."""
import bleach

from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from assets import mixins
from assets import models


class RenameFolderForm(mixins.RenameObjectMixin, forms.ModelForm):
    """Form for rename folder."""

    class Meta:
        model = models.Folder
        fields = ['title']


class UpdateShareForm(forms.ModelForm):
    """Form for update ShareTable."""

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
    """Form for create ShareTable."""

    def __init__(self, user=None, *args, **kwargs):
        """Override __init__ method for add user."""
        self.user = user
        super().__init__(*args, **kwargs)

    email = forms.EmailField()
    expired = forms.DateTimeField(input_formats=['%Y-%m-%d %H:%M'],
                                  widget=forms.DateTimeInput(attrs={'placeholder': 'year-m-d hours:min'}))
    permissions = forms.ModelMultipleChoiceField(queryset=models.Permissions.objects.all(),
                                                 widget=forms.CheckboxSelectMultiple)

    def clean_email(self):
        """Validate email field for user exists and sharing with yourself."""
        if self.cleaned_data['email'] == self.user.email:
            raise forms.ValidationError('Cannot share with yourself.')

        return self.cleaned_data['email']

    def clean_expired(self):
        if self.cleaned_data['expired'] < timezone.now():
            raise forms.ValidationError('Cannot be less then now.')

        return self.cleaned_data['expired']


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


class InputNameForm(mixins.RenameObjectMixin, forms.Form):
    """Form for create new folder."""

    title = forms.CharField(label='title', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
