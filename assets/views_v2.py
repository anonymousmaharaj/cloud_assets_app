"""Views for assets app."""

from django import http, views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

from assets import forms, models


class RenameFolderView(LoginRequiredMixin, views.View):
    """Class-based view for renaming folder."""

    login_url = '/login/'

    def get(self, request, folder_id: int):
        """Return the form related to the Folder model.

        @param request: default django request.
        @param folder_id: model.Folder primary key
        @return: HTTPResponse
        """
        return render(
            request,
            'assets/rename_folder.html',
            context={'form': forms.RenameFolderForm(
                instance=models.Folder.objects.filter(pk=folder_id).first())
            }
        )

    def post(self, request, folder_id: int):
        """Rename the folder or returns an error.

        @param request: default django request.
        @param folder_id: model.Folder primary key
        @return: HTTPResponse
        """
        folder = models.Folder.objects.filter(pk=folder_id).first()
        if not folder:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                )
            )
        if not folder.owner == request.user:
            return http.HttpResponseForbidden(
                content=render(
                    request=request,
                    template_name='assets/errors/403_error_page.html'
                )
            )
        form = forms.RenameFolderForm(request.POST, instance=folder)
        if not form.is_valid():
            return render(
                request,
                'assets/rename_folder.html',
                context={'form': form}
            )
        try:
            form.full_clean()
        except ValidationError:
            return render(
                request,
                'assets/rename_folder.html',
                context={'form': form}
            )
        form.save()
        if folder.parent is not None:
            return redirect(f'/?folder={folder.parent.pk}')
        else:
            return redirect('root_page')
