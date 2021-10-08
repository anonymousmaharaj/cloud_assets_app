"""Views for assets app."""
import logging

from django import http, views
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import F
from django.shortcuts import redirect, render, get_object_or_404
from rest_framework import generics
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from assets import forms
from assets import models
from assets import permissions
from assets import serializers
from assets.aws import s3
from assets.utils import create_file_relative_key

logger = logging.getLogger(__name__)


class UpdateShareView(LoginRequiredMixin, views.View):
    login_url = '/login/'

    def get(self, request, share_id):
        share = get_object_or_404(models.SharedTable, id=share_id)
        owned_shared_rows = models.SharedTable.objects.filter(
            file_id__in=[file.id for file in request.user.files.all()]
        )
        if share not in owned_shared_rows:
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )

        return render(
            request,
            'assets/update_share.html',
            context={'form': forms.UpdateShareForm(instance=share)}
        )

    def post(self, request, share_id):
        share = get_object_or_404(models.SharedTable, id=share_id)
        owned_shared_rows = models.SharedTable.objects.filter(
            file_id__in=[file.id for file in request.user.files.all()]
        )
        if share not in owned_shared_rows:
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )
        form = forms.UpdateShareForm(request.POST, instance=share)
        if not form.is_valid():
            logger.warning(f'[{request.user.username}] send invalid form \n {form.errors}.')
            return render(request, 'assets/share_file.html', context={'form': form})

        form.save()
        messages.success(request, 'This share was updated successfully.')
        return redirect('share-list')


class ListShareView(LoginRequiredMixin, views.View):
    login_url = '/login/'

    def get(self, request):
        return render(request,
                      'assets/share_details.html',
                      {'rows': models.SharedTable.objects.filter(
                          file_id__in=[file.id for file in request.user.files.all()])}
                      )


class DeleteShareView(LoginRequiredMixin, views.View):
    login_url = '/login/'

    def get(self, request, share_id):
        share = get_object_or_404(models.SharedTable, id=share_id)
        owned_shared_rows = models.SharedTable.objects.filter(
            file_id__in=[file.id for file in request.user.files.all()]
        )
        if share not in owned_shared_rows:
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )
        share.delete()
        messages.success(request, 'This share was deleted successfully.')
        return redirect('share-list')


class CreateShareView(LoginRequiredMixin, views.View):
    login_url = '/login/'

    def get(self, request, file_id: int):
        file = models.File.objects.filter(pk=file_id).first()
        if not file:
            logger.warning(f'[{request.user.username}] try to rename is not exist folder - ID: {file_id}')
            return http.HttpResponseNotFound(
                content=render(request=request, template_name='assets/errors/404_error_page.html')
            )
        if not file.owner == request.user:
            logger.warning(f'[{request.user.username}] try to get access to the denied file - ID: {file_id} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )

        return render(
            request,
            'assets/share_file.html',
            context={'form': forms.CreateShareForm()}
        )

    def post(self, request, file_id: int):
        file = models.File.objects.filter(pk=file_id).first()
        if not file:
            logger.warning(f'[{request.user.username}] try to share file is not exist. - ID: {file_id}')
            return http.HttpResponseNotFound(
                content=render(request=request, template_name='assets/errors/404_error_page.html')
            )
        if not file.owner == request.user:
            logger.warning(f'[{request.user.username}] try to get access to the denied file - ID: {file_id} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )

        form = forms.CreateShareForm(request.user,
                                     request.POST)

        if not form.is_valid():
            logger.warning(f'[{request.user.username}] send invalid form \n {form.errors}.')
            return render(request, 'assets/share_file.html', context={'form': form})

        try:
            instance = models.SharedTable.objects.create(
                file_id=file_id,
                user=User.objects.get(email=form.cleaned_data['email']),
                expired=form.cleaned_data['expired'],
            )
            instance.permissions.set(form.cleaned_data['permissions'])
            instance.save()
        except IntegrityError as e:
            logger.exception(f'[{request.user.username}] {str(e)} ')
            messages.error(request, 'Current share already exists.')
            return redirect('root_page')

        messages.success(request, 'The File was shared successfully.')
        return redirect('root_page')


class DownloadShareFileView(LoginRequiredMixin, views.View):
    login_url = '/login/'

    def get(self, request, file_id):
        if not models.SharedTable.objects.filter(
                file_id=file_id,
                user=request.user.pk,
                permissions__name='read_only').exists():
            logger.warning(f'[{request.user.username}] try to get access to the denied file - ID: {file_id} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )
        download_url = s3.get_url(file_id)

        return redirect(download_url)


class RenameShareFileView(LoginRequiredMixin, views.View):
    login_url = '/login/'

    def get(self, request, file_id):
        if not models.SharedTable.objects.filter(
                file_id=file_id,
                user=request.user.pk,
                permissions__name='rename_only').exists():
            logger.warning(f'[{request.user.username}] try to get access to the denied file - ID: {file_id} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )
        return render(
            request,
            'assets/rename_file.html',
            context={'form': forms.RenameFileForm()}
        )

    def post(self, request, file_id):
        file = get_object_or_404(models.File, pk=file_id)

        if not models.SharedTable.objects.filter(
                file_id=file_id,
                user=request.user.pk,
                permissions__name='rename_only'
        ).exists():
            logger.warning(f'[{request.user.username}] try to get access to the denied file - ID: {file_id} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )

        form = forms.RenameFileForm(request.POST)
        if not form.is_valid():
            logger.warning(f'[{request.user.username}] send invalid form \n {form.errors}.')
            return render(request, 'assets/rename_file.html', context={'form': form})

        file.title = form.cleaned_data['new_title']
        file.save()
        return redirect('root_page')


class DeleteShareFileView(LoginRequiredMixin, views.View):
    login_url = '/login/'

    def get(self, request, file_id):
        file = get_object_or_404(models.File, pk=file_id)

        if not models.SharedTable.objects.filter(
                file_id=file_id,
                user=request.user.pk,
                permissions__name='delete_only').exists():
            logger.warning(f'[{request.user.username}] try to get access to the denied file - ID: {file_id} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )
        share = models.SharedTable.objects.filter(file_id=file_id, user=request.user.pk).first()

        share.delete()
        file.delete()
        return redirect('root_page')


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


class FolderRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """View for rename folder's endpoint."""

    queryset = models.Folder.objects.all()
    permission_classes = (permissions.IsObjectOwner, permissions.IsParentOwner, IsAuthenticated)
    serializer_class = serializers.FolderRetrieveUpdateSerializer


class FolderListCreateView(generics.ListCreateAPIView):
    """Generic APIView for List and Create folders."""

    queryset = models.Folder.objects.all()
    permission_classes = (permissions.IsParentOwner, IsAuthenticated)
    serializer_class = serializers.FolderListCreateSerializer
    parser_classes = (JSONParser,)

    def get_queryset(self):
        """Filter objects by user."""
        return models.Folder.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Override this method to save additional fields."""
        serializer.save(owner=self.request.user)


class FileRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """View for rename folder's endpoint."""

    queryset = models.File.objects.all()
    permission_classes = (permissions.IsObjectOwner, permissions.IsFolderOwner, IsAuthenticated)
    serializer_class = serializers.FileRetrieveUpdateDestroySerializer


class FileListCreateView(generics.ListCreateAPIView):
    """Generic APIView for List and Create files."""

    queryset = models.File.objects.all()
    permission_classes = (permissions.IsFolderOwner, IsAuthenticated)
    serializer_class = serializers.FileListCreateSerializer

    def get_queryset(self):
        """Filter objects by user."""
        return models.File.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Override this method to save additional fields."""
        rk = create_file_relative_key(self.request.user.pk)
        serializer.save(owner=self.request.user,
                        relative_key=rk)


class ShareListCreateView(generics.ListCreateAPIView):
    queryset = models.SharedTable.objects.all()
    permission_classes = (permissions.IsShareOwner, permissions.IsSharingFileOwner, IsAuthenticated)
    serializer_class = serializers.ShareListCreateSerializer

    def get_queryset(self):
        """Filter objects by user."""

        return models.SharedTable.objects.filter(
            file_id__in=[file.id for file in self.request.user.files.all()],
            created_at__lt=F('expired')
        )


class ShareRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """View for rename folder's endpoint."""

    queryset = models.SharedTable.objects.all()
    permission_classes = (permissions.IsShareOwner, IsAuthenticated)
    serializer_class = serializers.ShareRetrieveUpdateDestroySerializer

    def get_queryset(self):
        """Filter objects by user."""

        return models.SharedTable.objects.filter(
            file_id__in=[file.id for file in self.request.user.files.all()],
            created_at__lt=F('expired')
        )


class SharedFileRetrieveUpdateDestroyView(APIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        if not models.SharedTable.objects.filter(
                file_id=pk,
                user=request.user.pk,
                permissions__name='read_only').exists():
            raise PermissionDenied(detail='forbidden')

        return Response({'url': s3.get_url(pk)})

    def put(self, request, pk):
        if not models.SharedTable.objects.filter(
                file_id=pk,
                user=request.user.pk,
                permissions__name='rename_only').exists():
            raise PermissionDenied(detail='forbidden')

        # data = {'title': request.data.get('title')}
        instance = models.File.objects.get(pk=pk)
        serializer = serializers.ShareFileUpdateSerializer(instance=instance,
                                                           data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'title': instance.title})

    def delete(self, request, pk):
        if not models.SharedTable.objects.filter(
                file_id=pk,
                user=request.user.pk,
                permissions__name='delete_only').exists():
            raise PermissionDenied(detail='forbidden')

        models.SharedTable.objects.filter(file_id=pk, user=request.user).first().delete()
        models.File.objects.get(pk=pk).delete()

        return Response({'detail': 'deleted'}, status=status.HTTP_204_NO_CONTENT)


class GetThumbnailView(APIView):

    def post(self, request, uuid):
        s3.check_exists(request.data.get('thumbnail_key'))
        instance = models.File.objects.filter(relative_key__contains=uuid).first()

        if not instance:
            raise ParseError(detail=f'File with {uuid} key does not exist.')

        serializer = serializers.ThumbnailSerializer(instance,
                                                     data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        logger.info(f'{request.data.get("thumbnail_key")} was created.')
        return Response({'detail': 'success'}, status=status.HTTP_200_OK)
