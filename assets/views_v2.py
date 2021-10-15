"""Views for assets app."""
import logging
import os

from django import http, views
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework import generics
from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework import mixins
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from assets import forms
from assets import models
from assets import permissions
from assets import serializers
from assets.aws import s3
from assets.db import queries
from assets.utils import create_file_relative_key

logger = logging.getLogger(__name__)


class UpdateShareView(LoginRequiredMixin, views.View):
    """Update share object."""

    login_url = '/login/'

    def get(self, request, share_id):
        """Create empty form."""
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
        """Update share object."""
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
    """List of shares."""

    login_url = '/login/'

    def get(self, request):
        """List of shares."""
        return render(request,
                      'assets/share_details.html',
                      {'rows': models.SharedTable.objects.filter(
                          file_id__in=[file.id for file in request.user.files.all()])}
                      )


class DeleteShareView(LoginRequiredMixin, views.View):
    """Delete share."""

    login_url = '/login/'

    def get(self, request, share_id):
        """Delete share."""
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
    """Create ShareTable."""

    login_url = '/login/'

    def get(self, request, uuid):
        """Create empty form."""
        file = models.File.objects.filter(relative_key__contains=uuid).first()
        if not file:
            logger.warning(f'[{request.user.username}] try to rename is not exist folder - UUID: {uuid}')
            return http.HttpResponseNotFound(
                content=render(request=request, template_name='assets/errors/404_error_page.html')
            )
        if not file.owner == request.user:
            logger.warning(f'[{request.user.username}] try to get access to the denied file - UUID: {uuid} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )

        return render(
            request,
            'assets/share_file.html',
            context={'form': forms.CreateShareForm()}
        )

    def post(self, request, uuid):
        """Create ShareTable."""
        file = models.File.objects.filter(relative_key__contains=uuid).first()
        if not file:
            logger.warning(f'[{request.user.username}] try to share file is not exist. - UUID: {uuid}')
            return http.HttpResponseNotFound(
                content=render(request=request, template_name='assets/errors/404_error_page.html')
            )
        if not file.owner == request.user:
            logger.warning(f'[{request.user.username}] try to get access to the denied file - UUID: {uuid} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )

        form = forms.CreateShareForm(request.user,
                                     request.POST)

        if not form.is_valid():
            logger.warning(f'[{request.user.username}] send invalid form \n {form.errors}.')
            return render(request, 'assets/share_file.html', context={'form': form})

        shared_user = User.objects.filter(email=form.cleaned_data['email']).first()

        if not shared_user:
            messages.success(request, 'The File was shared successfully.')
            return redirect('root_page')

        try:
            instance = models.SharedTable.objects.create(
                file_id=file.pk,
                user=shared_user,
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
    """Get a shared file."""

    login_url = '/login/'

    def get(self, request, uuid):
        """Get a shared file."""
        if not models.SharedTable.objects.filter(
                file__relative_key__contains=uuid,
                user=request.user.pk,
                permissions__name=models.Permissions.READ_ONLY).exists():
            logger.warning(f'[{request.user.username}] try to get access to the denied file - ID: {uuid} .')
            return http.HttpResponseForbidden(
                content=render(request=request, template_name='assets/errors/403_error_page.html')
            )
        download_url = s3.get_url(uuid)

        return redirect(download_url)


class RenameShareFileView(LoginRequiredMixin, views.View):
    """Rename a shared file."""

    login_url = '/login/'

    def get(self, request, file_id):
        """Create empty form."""
        if not models.SharedTable.objects.filter(
                file_id=file_id,
                user=request.user.pk,
                permissions__name=models.Permissions.READ_ONLY).exists():
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
        """Rename file."""
        file = get_object_or_404(models.File, pk=file_id)

        if not models.SharedTable.objects.filter(
                file_id=file_id,
                user=request.user.pk,
                permissions__name=models.Permissions.RENAME_ONLY).exists():
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
    """Delete a shared file."""

    login_url = '/login/'

    def get(self, request, file_id):
        """Delete a shared file."""
        file = get_object_or_404(models.File, pk=file_id)

        if not models.SharedTable.objects.filter(
                file_id=file_id,
                user=request.user.pk,
                permissions__name=models.Permissions.DELETE_ONLY).exists():
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
    permission_classes = (permissions.IsObjectOwner, IsAuthenticated)
    serializer_class = serializers.FolderRetrieveUpdateSerializer


class FolderListCreateView(generics.ListCreateAPIView):
    """Generic APIView for List and Create folders."""

    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.FolderListCreateSerializer
    parser_classes = (JSONParser,)

    def get_queryset(self):
        """Filter objects by user."""
        return models.Folder.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Override this method to save additional fields."""
        serializer.is_valid(raise_exception=True)
        parent = serializer.validated_data.get('parent')
        if parent is not None:
            if not self.request.user.folders.filter(pk=parent.pk):
                raise PermissionDenied(detail='You do not have permission to perform this action.')
        serializer.save(owner=self.request.user)


class FileRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """View for rename file's endpoint."""

    queryset = models.File.objects.all()
    permission_classes = (permissions.IsObjectOwner, IsAuthenticated)
    serializer_class = serializers.FileRetrieveUpdateDestroySerializer

    def perform_update(self, serializer):
        serializer.is_valid(raise_exception=True)
        folder = serializer.validated_data.get('folder')
        if folder is not None:
            if not self.request.user.folders.filter(pk=folder.pk):
                raise PermissionDenied(detail='You do not have permission to perform this action.')


class FileListCreateView(generics.ListCreateAPIView):
    """Generic APIView for List and Create files."""

    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.FileListCreateSerializer

    def get_queryset(self):
        """Filter objects by user."""
        return models.File.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """Override this method to save additional fields."""
        serializer.is_valid(raise_exception=True)
        folder = serializer.validated_data.get('folder')
        if folder is not None:
            if not self.request.user.folders.filter(pk=folder.pk):
                raise PermissionDenied(detail='You do not have permission to perform this action.')

        rk = create_file_relative_key(self.request.user.pk)
        extension = os.path.splitext(serializer.validated_data.get('title'))[1]
        size = serializer.validated_data.get('size')

        serializer.save(owner=self.request.user,
                        relative_key=rk,
                        extension=extension,
                        size=size)


class ShareListCreateView(generics.ListCreateAPIView):
    """Create and list for ShareTable."""

    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ShareListCreateSerializer

    def get_queryset(self):
        """Filter objects by user."""
        queries.delete_expired_shares()
        now = timezone.now()
        return models.SharedTable.objects.filter(
            file__owner=self.request.user,
            expired__gt=now
        )

    def create(self, request, *args, **kwargs):
        """Override 'create' method to return 201 Created to exclude payload."""
        super(ShareListCreateView, self).create(request, *args, **kwargs)
        return Response(status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        file = serializer.validated_data.get('file')
        if not self.request.user.files.filter(pk=file.pk):
            raise PermissionDenied(detail='You do not have permission to perform this action.')

        if not User.objects.filter(email=serializer.validated_data.get('email')).exists():
            return

        super(ShareListCreateView, self).perform_create(serializer)


class ShareUpdateDestroyView(mixins.DestroyModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    """View for rename folder's endpoint."""

    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ShareUpdateDestroySerializer

    def get_queryset(self):
        """Filter objects by user."""
        return models.SharedTable.objects.filter(file__owner=self.request.user)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class SharedFileRetrieveUpdateDestroyView(APIView):
    """Interact with shared file."""

    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        """Get download URL for a shared file."""
        if not models.SharedTable.objects.filter(
                file_id=pk,
                user=request.user.pk,
                permissions__name=models.Permissions.READ_ONLY).exists():
            raise PermissionDenied(detail='You do not have permission to perform this action.')

        return Response({'url': s3.get_url(pk)})

    def put(self, request, pk):
        """Rename file if permission is okay."""
        if not models.SharedTable.objects.filter(
                file_id=pk,
                user=request.user.pk,
                permissions__name=models.Permissions.RENAME_ONLY).exists():
            raise PermissionDenied(detail='You do not have permission to perform this action.')

        instance = models.File.objects.get(pk=pk)
        serializer = serializers.ShareFileUpdateSerializer(instance=instance,
                                                           data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'title': instance.title})

    def delete(self, request, pk):
        """Delete file if permission is okay."""
        if not models.SharedTable.objects.filter(
                file_id=pk,
                user=request.user.pk,
                permissions__name=models.Permissions.DELETE_ONLY).exists():
            raise PermissionDenied(detail='You do not have permission to perform this action.')

        queries.delete_shared_table(pk)
        queries.delete_file(pk)

        return Response({'detail': 'deleted'}, status=status.HTTP_204_NO_CONTENT)


class ListSharedFilesView(generics.ListAPIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.RetrieveListSharedFilesSerializer

    def get_queryset(self):
        return models.SharedTable.objects.filter(
            user=self.request.user,
            created_at__lt=F('expired')
        )


class CreateThumbnailView(APIView):
    """Create thumbnail in db with aws lambda."""

    # TODO: Add lambda permissions.
    def post(self, request, uuid):
        """Write a thumbnail in DB."""
        serializer = serializers.ThumbnailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        thumbnail_key = serializer.validated_data['thumbnail_key']
        instance = get_object_or_404(models.File, relative_key__contains=uuid)
        s3.check_exists(thumbnail_key)

        instance.thumbnail_key = thumbnail_key
        instance.save()

        logger.info(f'{request.data.get("thumbnail_key")} was created.')
        return Response({'detail': 'success'}, status=status.HTTP_200_OK)


class FileRetrieveUpdateDestroyView(APIView):
    """View for retrieve update and destroy file obj."""

    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, uuid):
        """Get download URL for a shared file."""
        if not models.File.objects.filter(
                relative_key__contains=uuid,
                owner=request.user.pk).exists():
            raise PermissionDenied(detail='forbidden')

        return Response({'url': s3.get_url(uuid)})

    def put(self, request, uuid):
        """Rename file if permission is okay."""
        if not models.File.objects.filter(
                relative_key__contains=uuid,
                owner=request.user.pk).exists():
            raise PermissionDenied(detail='forbidden')

        instance = models.File.objects.filter(relative_key__contains=uuid).first()

        serializer = serializers.FileRetrieveUpdateDestroySerializer(instance=instance,
                                                                     data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'title': instance.title})

    def delete(self, request, uuid):
        """Delete file if permission is okay."""
        if not models.File.objects.filter(
                relative_key__contains=uuid,
                owner=request.user.pk).exists():
            raise PermissionDenied(detail='forbidden')

        s3.delete_key(uuid)
        queries.delete_shared_table(uuid)
        queries.delete_file(uuid)

        return Response(status=status.HTTP_204_NO_CONTENT)


class FileListCreateView(APIView):
    authentication_classes = (BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        files = models.File.objects.filter(owner=request.user)
        for file in files:
            file.relative_key = file.relative_key.split('/')[-1]
        serializer = serializers.NewFileListCreateSerializer(files, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = serializers.NewFileListCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        folder = serializer.validated_data.get('folder')
        if folder is not None:
            if not self.request.user.folders.filter(pk=folder.pk):
                raise PermissionDenied(detail='You do not have permission to perform this action.')

        rk = create_file_relative_key(self.request.user.pk)
        extension = os.path.splitext(serializer.validated_data.get('title'))[1]
        size = serializer.validated_data.get('size')

        serializer.save(owner=self.request.user,
                        relative_key=rk,
                        extension=extension,
                        size=size)

        return Response(data=serializer.data, status=HTTP_201_CREATED)
