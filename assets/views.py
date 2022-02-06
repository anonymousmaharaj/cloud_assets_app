"""Views for Assets application."""
import logging

from datetime import datetime
import os
import uuid

from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.db import IntegrityError

from assets import forms
from assets import models
from assets import validators
from assets.aws import s3
from assets.db import queries

logger = logging.getLogger(__name__)


def health_check(request):
    """Response 200 status code."""
    return http.JsonResponse({'server_status': 200})


@login_required(login_url='/login/')
def show_page(request):
    """Render page for display assets."""
    profile.enable()
    now = datetime.now()

    folder_id = request.GET.get('folder')

    validate_params_status = validators.validate_get_params(dict(request.GET))

    if not validate_params_status:
        return http.HttpResponseBadRequest(
            content=render(
                request=request,
                template_name='assets/errors/400_error_page.html'
            ))

    folder_obj = get_object_or_404(models.Folder,
                                   uuid=folder_id) if folder_id else None

    queries.delete_expired_shares()

    rows = queries.get_assets_list(folder_id, request.user.pk)

    rows = s3.get_thumbnails(rows, request.user)

    shared_rows = models.SharedTable.objects.filter(user=request.user,
                                                    created_at__lt=F('expired'))
    for row in shared_rows:
        row.file.relative_key = row.file.relative_key.split('/')[-1]

    context = {'rows': rows, 'folder_obj': folder_obj, 'shared_rows': shared_rows}

    profile.disable()
    profile.dump_stats(f'profilers/{__name__}_show_page_{now}.prof')
    return render(request, 'assets/root_page.html', context)


@login_required(login_url='/login/')
def user_upload_file(request):
    """Upload file to S3.

    Render form. Get file's path and upload it on S3.
    Create new object in File table.
    """

    if request.method == 'POST':

        profile.enable()
        now = datetime.now()

        form = forms.UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            parent_folder = request.GET.get('folder')

            if parent_folder == '':
                parent_folder = None

            uploaded_file = request.FILES.get('file', None)
            if uploaded_file is None:
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            file_name = uploaded_file.name

            parent_folder_instance = models.Folder.objects.filter(uuid=parent_folder).first()
            file_exist = validators.validate_exist_file_in_folder(
                file_name,
                user=request.user,
                folder=parent_folder_instance)

            if file_exist:
                messages.error(request, 'The file already exists.')
                return redirect('root_page')

            folder_exists = models.Folder.objects.filter(
                uuid=parent_folder).exists()

            if folder_exists:
                parent_folder = models.Folder.objects.get(uuid=parent_folder)
            else:
                parent_folder = None

            file_key = f'users/{request.user.pk}/assets/{str(uuid.uuid4())}'

            if s3.upload_file(uploaded_file.file,
                              file_key,
                              os.path.splitext(uploaded_file.name)[1],
                              uploaded_file.content_type):
                queries.create_file(file_name,
                                    request.user,
                                    parent_folder,
                                    file_key,
                                    uploaded_file.size,
                                    os.path.splitext(uploaded_file.name)[1])
                messages.success(request, 'The file was uploaded.')

                profile.disable()
                profile.dump_stats(f'profilers/{__name__}_upload_file_{now}.prof')

                if parent_folder is not None:
                    return redirect(f'/?folder={parent_folder.uuid}')
                else:
                    return redirect('root_page')
            else:
                return http.HttpResponse(
                    'Your file already exist in target directory.'
                )
        else:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                ))
    elif request.method == 'GET':
        form = forms.UploadFileForm()
        parent_folder = request.GET.get('folder')
        context = {'form': form,
                   'parent_folder': parent_folder}
        return render(request,
                      'assets/upload_file.html',
                      context=context)
    else:
        return http.HttpResponseNotAllowed(['GET', 'POST'])


@login_required(login_url='/login/')
def create_folder(request):
    """View for create new folder."""
    if request.method == 'POST':
        form = forms.InputNameForm(request.POST)
        if form.is_valid():
            parent_folder = request.GET.get('folder')
            new_folder_title = form.cleaned_data.get('title', None)

            if new_folder_title is None:
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            new_folder_title = new_folder_title.strip()

            if parent_folder == '':
                parent_folder = None

            params_status = validators.validate_get_params(
                dict(request.GET))
            folder_exist_status = validators.validate_parent_folder(
                parent_folder)
            parent_folder_exist_status = validators.validate_exist_current_folder(parent_folder)
            title_exist_status = validators.validate_exist_parent_folder(
                parent_folder,
                new_folder_title,
                request.user)

            if title_exist_status:
                return http.HttpResponse(
                    'Folder with this title already exist '
                    'in target directory.')

            if (not parent_folder_exist_status or
                    not params_status or
                    not folder_exist_status):
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))
            parent_folder_instance = models.Folder.objects.filter(uuid=parent_folder).first()

            queries.create_folder(request.user, new_folder_title, parent_folder_instance)
            messages.success(request, 'The folder was created.')
            if parent_folder_instance is not None:
                return redirect(f'/?folder={parent_folder_instance.uuid}')
            else:
                return redirect('root_page')
        else:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                ))
    elif request.method == 'GET':
        form = forms.InputNameForm()
        parent_folder = request.GET.get('folder')
        context = {'form': form,
                   'parent_folder': parent_folder}
        return render(request,
                      'assets/create_folder.html',
                      context=context)
    else:
        return http.HttpResponseNotAllowed(['GET', 'POST'])


@login_required(login_url='/login/')
def download_file(request):
    """View for download file."""
    if request.method == 'GET':
        file_uuid = request.GET.get('file')

        validate_file_exist_status = validators.validate_exist_file(
            request.user,
            file_uuid
        )
        validate_params_status = validators.validate_get_params(dict(request.GET))
        validate_permission_status = validators.validate_file_permission(
            request.user,
            file_uuid
        )

        if not validate_permission_status:
            return http.HttpResponseForbidden(
                content=render(
                    request=request,
                    template_name='assets/errors/403_error_page.html'
                ))

        if not validate_file_exist_status:
            return http.HttpResponseNotFound(
                content=render(
                    request=request,
                    template_name='assets/errors/404_error_page.html'
                ))

        if not validate_params_status:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                ))

        download_url = s3.get_url(file_uuid)

        return redirect(download_url)
    else:
        return http.HttpResponseNotAllowed(['GET'])


@login_required(login_url='/login/')
def delete_file(request):
    """View for delete file."""
    if request.method == 'GET':
        file_uuid = request.GET.get('file')

        validate_file_exist_status = validators.validate_exist_file(
            request.user,
            file_uuid
        )
        validate_params_status = validators.validate_get_params(dict(request.GET))
        validate_permission_status = validators.validate_file_permission(
            request.user,
            file_uuid
        )

        if not validate_permission_status:
            return http.HttpResponseForbidden(
                content=render(
                    request=request,
                    template_name='assets/errors/403_error_page.html'
                ))

        if not validate_file_exist_status:
            return http.HttpResponseNotFound(
                content=render(
                    request=request,
                    template_name='assets/errors/404_error_page.html'
                ))

        if not validate_params_status:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                ))

        file_obj = models.File.objects.filter(relative_key__contains=file_uuid).first()
        folder_uuid = file_obj.folder.uuid if file_obj.folder else None

        try:
            with transaction.atomic():
                queries.delete_shared_table(file_uuid)
                queries.delete_file(file_uuid)
        except IntegrityError as e:
            logger.exception(f'Exception while deleting file {file_uuid}. {str(e)}')
            messages.error(request, 'Cannot delete file. Try again. ')
            return redirect('root_page')
        else:
            s3.delete_key(file_uuid)

        messages.success(request, 'The file was successfully deleted. ')
        if folder_uuid is not None:
            return redirect(f'/?folder={folder_uuid}')
        else:
            return redirect('root_page')

    else:
        return http.HttpResponseNotAllowed(['GET'])


@login_required(login_url='/login/')
def delete_folder(request):
    """Delete folder with all files inside."""
    if request.method == 'GET':
        folder_uuid = request.GET.get('folder')

        params_status = validators.validate_get_params(
            dict(request.GET))
        folder_exist_status = validators.validate_parent_folder(folder_uuid)
        folder_permission_status = validators.validate_folder_permission(
            request.user,
            folder_uuid
        )

        if not folder_permission_status:
            return http.HttpResponseForbidden(
                content=render(
                    request=request,
                    template_name='assets/errors/403_error_page.html'
                ))

        if (not params_status or
                not folder_exist_status or
                not params_status):
            return http.HttpResponseBadRequest(content=render(
                request=request,
                template_name='assets/errors/400_error_page.html'
            ))

        folder_obj = models.Folder.objects.get(uuid=folder_uuid)
        parent_uuid = folder_obj.parent.uuid if folder_obj.parent else None

        try:
            with transaction.atomic():
                s3.delete_recursive(folder_uuid)
        except IntegrityError as e:
            logger.exception(f'Exception while deleting folder {folder_uuid}. {str(e)}')
            messages.error(request, 'Cannot delete file. Try again. ')
            return redirect('root_page')

        messages.success(request, 'The folder was successfully deleted. ')
        if parent_uuid is not None:
            return redirect(f'/?folder={parent_uuid}')
        else:
            return redirect('root_page')

    else:
        return http.HttpResponseNotAllowed(['GET'])


@login_required(login_url='/login/')
def move_file(request):
    """View for move file."""
    """View for move file."""
    if request.method == 'POST':
        form = forms.MoveFileForm(request.POST, user=request.user)
        if form.is_valid():
            new_folder = form.cleaned_data.get('new_folder', None)
            file_uuid = request.GET.get('file', None)

            if (new_folder is None or
                    file_uuid is None):
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            if new_folder == 'None':
                new_folder = None

            folder_exist_status = validators.validate_parent_folder(new_folder)
            file_permission_status = validators.validate_file_permission(
                request.user,
                file_uuid
            )
            file_exist_status = validators.validate_exist_file(request.user, file_uuid)
            params_status = validators.validate_get_params(dict(request.GET))

            if file_exist_status and folder_exist_status:
                file = models.File.objects.filter(relative_key__contains=file_uuid).first()
                if new_folder is not None:
                    new_folder = models.Folder.objects.filter(uuid=new_folder).first()
                file_name = file.title
                file_exist_in_folder = validators.validate_exist_file_in_folder(
                    file_name=file_name,
                    user=request.user,
                    folder=new_folder)
                if file_exist_in_folder:
                    return http.HttpResponse('File already exist in target directory')

            if new_folder is not None:
                folder_permission_status = validators.validate_folder_permission(
                    request.user,
                    new_folder.uuid
                )
            else:
                folder_permission_status = True

            if not folder_permission_status or not file_permission_status:
                return http.HttpResponseForbidden(
                    content=render(
                        request=request,
                        template_name='assets/errors/403_error_page.html'
                    ))

            if (not folder_exist_status or
                    not file_exist_status or
                    not params_status):
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))
            old_folder = file.folder
            queries.move_file(new_folder, file_uuid)
            messages.success(request, 'The file was successfully moved. ')
            if old_folder is not None:
                return redirect(f'/?folder={old_folder.uuid}')
            else:
                return redirect('root_page')

    elif request.method == 'GET':
        form = forms.MoveFileForm(user=request.user)
        context = {'form': form}
        return render(request,
                      'assets/move_file.html',
                      context=context)
    else:
        return http.HttpResponseNotAllowed(['GET', 'POST'])


@login_required(login_url='/login/')
def rename_file(request):
    """View for rename file."""
    if request.method == 'POST':
        form = forms.InputNameForm(request.POST)
        if form.is_valid():
            new_title = form.cleaned_data.get('title', None)
            file_uuid = request.GET.get('file', None)

            if (new_title is None or
                    file_uuid is None):
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            new_title = new_title.strip()
            file_permission_status = validators.validate_file_permission(
                request.user,
                file_uuid
            )
            file_exist_status = validators.validate_exist_file(request.user, file_uuid)
            params_status = validators.validate_get_params(dict(request.GET))

            if (not file_exist_status or
                    not params_status):
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            if not file_permission_status:
                return http.HttpResponseForbidden(
                    content=render(
                        request=request,
                        template_name='assets/errors/403_error_page.html'
                    ))

            if file_exist_status:
                file = models.File.objects.filter(relative_key__contains=file_uuid).first()
                folder = file.folder
                file_exist_in_folder = validators.validate_exist_file_in_folder(new_title,
                                                                                request.user,
                                                                                folder=folder)
                if file_exist_in_folder:
                    return http.HttpResponse('File already exists in folder. Change name.')

            queries.rename_file(file_uuid, new_title)
            messages.success(request, 'The file was successfully renamed. ')
            if folder is not None:
                return redirect(f'/?folder={folder.uuid}')
            else:
                return redirect('root_page')

        else:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                ))

    elif request.method == 'GET':
        form = forms.InputNameForm()
        context = {'form': form}
        return render(request,
                      'assets/rename_file.html',
                      context=context)
    else:
        return http.HttpResponseNotAllowed(['GET', 'POST'])


@login_required(login_url='/login/')
def rename_folder(request):
    """View for rename folder."""
    if request.method == 'POST':
        form = forms.RenameFolderForm(request.POST)
        if form.is_valid():
            new_title = form.cleaned_data.get('new_title', None)
            folder_uuid = request.GET.get('folder', None)

            if (new_title is None or
                    folder_uuid is None):
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            new_title = new_title.strip()

            folder_permission_status = validators.validate_folder_permission(
                request.user,
                folder_uuid
            )
            folder_exist_status = validators.validate_exist_current_folder(
                folder_uuid)
            params_status = validators.validate_get_params(dict(request.GET))
            new_folder_exist = validators.validate_exist_folder_new_title(
                folder_uuid,
                new_title,
                request.user
            )

            if new_folder_exist:
                return http.HttpResponse('Cannot rename folder. Check current directory '
                                         'for same title.')

            if (not params_status or
                    not folder_exist_status):
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            if not folder_permission_status:
                return http.HttpResponseForbidden(
                    content=render(
                        request=request,
                        template_name='assets/errors/403_error_page.html'
                    ))
            current_folder = models.Folder.objects.get(pk=folder_uuid)
            queries.rename_folder(folder_uuid, new_title)
            messages.success(request, 'The folder was successfully renamed. ')
            if current_folder.parent is not None:
                return redirect(f'/?folder={current_folder.parent.uuid}')
            else:
                return redirect('root_page')

        else:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                ))

    elif request.method == 'GET':
        form = forms.RenameFolderForm()
        context = {'form': form}
        return render(request,
                      'assets/rename_folder.html',
                      context=context)
    else:
        return http.HttpResponseNotAllowed(['GET', 'POST'])
