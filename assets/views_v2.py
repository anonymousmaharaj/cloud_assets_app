"""Views for assets app."""
import logging
import uuid

from django import http, views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import redirect, render
from rest_framework import generics

from assets import forms
from assets import models
from assets import permissions
from assets import serializers

logger = logging.getLogger(__name__)


class RenameFolderView(LoginRequiredMixin, views.View):
    """Class-based view for renaming folder."""

    login_url = '/login/'

    def get(self, request, folder_id: int):
        """Return the form related to the Folder model.

        @param request: default django request.
        @param folder_id: model.Folder primary key
        @return: HTTPResponse
        """
        folder = models.Folder.objects.filter(pk=folder_id).first()
        if not folder:
            logger.warning(f'[{request.user.username}] try to rename is not exist folder - ID: {folder_id}')
            return http.HttpResponseNotFound(
                content=render(request=request, template_name='assets/errors/404_error_page.html')
            )
        if not folder.owner == request.user:
            logger.warning(f'[{request.user.username}] try to get access to the denied folder - ID: {folder_id} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )

        return render(
            request,
            'assets/rename_folder.html',
            context={'form': forms.RenameFolderForm(
                instance=models.Folder.objects.filter(pk=folder_id).first())}
        )

    def post(self, request, folder_id: int):
        """Rename the folder or returns an error.

        @param request: default django request.
        @param folder_id: model.Folder primary key
        @return: HTTPResponse
        """
        #
        folder = models.Folder.objects.filter(pk=folder_id).first()
        if not folder:
            logger.warning(f'[{request.user.username}] try to rename is not exist folder - ID: {folder_id}')
            return http.HttpResponseNotFound(
                content=render(request=request, template_name='assets/errors/404_error_page.html')
            )
        if not folder.owner == request.user:
            logger.warning(f'[{request.user.username}] try to get access to the denied folder - ID: {folder_id} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )

        form = forms.RenameFolderForm(request.POST, instance=folder)

        if not form.is_valid():
            logger.warning(f'[{request.user.username}] send invalid form \n {form.errors}.')
            return render(request, 'assets/rename_folder.html', context={'form': form})

        try:
            form.save()
        except IntegrityError as e:
            logger.exception(f'[{request.user.username}] {str(e)} ')
        return redirect('root_page' if folder.parent is None else f'/folder={folder.parent.pk}')


class FolderUpdate(generics.RetrieveUpdateAPIView):
    """View for rename folder's endpoint."""

    queryset = models.Folder.objects.all()
    permission_classes = (permissions.IsOwner, permissions.IsParentOwner)
    serializer_class = serializers.UpdateFolderSerializer


class FolderListCreate(generics.ListCreateAPIView):
    queryset = models.Folder.objects.all()
    permission_classes = (permissions.IsParentOwner,)
    serializer_class = serializers.ListCreateFolderSerializer

    def get_queryset(self):
        user = self.request.user
        return models.Folder.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FileUpdate(generics.RetrieveUpdateDestroyAPIView):
    """View for rename folder's endpoint."""

    queryset = models.File.objects.all()
    permission_classes = (permissions.IsOwner, permissions.IsFolderOwner)
    serializer_class = serializers.UpdateFileSerializer


class FileListCreate(generics.ListCreateAPIView):
    queryset = models.File.objects.all()
    permission_classes = (permissions.IsFolderOwner,)
    serializer_class = serializers.ListCreateFileSerializer

    def get_queryset(self):
        user = self.request.user
        return models.File.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user,
                        relative_key=f'users/{self.request.user.pk}/assets/{uuid.uuid4()}')
