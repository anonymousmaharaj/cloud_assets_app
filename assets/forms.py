"""Forms for Assets application."""

from django import forms


class UploadFileForm(forms.Form):
    """Form for input file's path."""

    path = forms.CharField(label='path')
