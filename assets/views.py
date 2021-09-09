"""Views for Assets application."""

import uuid

from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from assets import forms
from assets import models
from assets import validators
from assets.aws import s3
from assets.db import queries


def health_check(request):
    """Response 200 status code."""
    return http.JsonResponse({'server_status': 200})


@login_required(login_url='/login/')
def show_page(request):
    """Render page for display assets."""
    folder_id = request.GET.get('folder')

    validate_id_status = validators.validate_folder_id(folder_id)
    validate_params_status = validators.validate_get_params(dict(request.GET))

    if not validate_id_status or not validate_params_status:
        return http.HttpResponseBadRequest(
            content=render(
                request=request,
                template_name='assets/errors/400_error_page.html'
            ))

    folder_obj = get_object_or_404(models.Folder,
                                   pk=folder_id) if folder_id else None

    rows = queries.get_assets_list(folder_id, request.user.pk)
    context = {'rows': rows, 'folder_obj': folder_obj}
    return render(request, 'assets/root_page.html', context)


@login_required(login_url='/login/')
def user_upload_file(request):
    """Upload file to S3.

    Render form. Get file's path and upload it on S3.
    Create new object in File table.
    """
    # TODO: Add functionality to add to folder.
    if request.method == 'POST':
        form = forms.UploadFileForm(request.POST)
        if form.is_valid():
            parent_folder = request.GET.get('folder')
            if parent_folder == '':
                parent_folder = None

            upload_path = request.POST.get('path')

            id_status = validators.validate_id_for_folder(parent_folder)
            validate_status = validators.validate_upload_file(upload_path)
            file_exist = validators.validate_exist_file_in_folder(
                upload_path,
                user=request.user,
                folder=parent_folder)

            if not id_status:
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            if not validate_status:
                return http.HttpResponse(
                    f'No such file in directory {upload_path}')

            if file_exist:
                return http.HttpResponse('File already exist in folder.')

            folder_exists = models.Folder.objects.filter(
                pk=parent_folder).exists()
            if folder_exists:
                parent_folder = models.Folder.objects.get(pk=parent_folder)
            else:
                parent_folder = None

            file_key = f'users/{request.user.pk}/assets/{str(uuid.uuid4())}'

            if s3.upload_file(upload_path, request.user, file_key):
                queries.create_file(upload_path, request.user, parent_folder, file_key)
                return http.HttpResponse('Your file is uploaded.')
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
        form = forms.CreateFolderForm(request.POST)
        if form.is_valid():
            parent_folder = request.GET.get('folder')
            new_folder_title = request.POST.get('title', None)

            if new_folder_title is None:
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            new_folder_title = new_folder_title.strip()

            if parent_folder == '':
                parent_folder = None

            id_status = validators.validate_id_for_folder(
                parent_folder)
            params_status = validators.validate_get_params(
                dict(request.GET))
            name_status = validators.validate_new_name(
                new_folder_title)
            folder_exist_status = validators.validate_parent_folder(
                parent_folder)
            title_exist_status = validators.validate_exist_parent_folder(
                parent_folder,
                new_folder_title,
                request.user)

            if title_exist_status:
                return http.HttpResponse(
                    'Folder with this title already exist '
                    'in target directory.')

            if (not id_status or
                    not params_status or
                    not name_status or
                    not folder_exist_status):
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            models.Folder(title=new_folder_title,
                          owner=request.user,
                          parent_id=parent_folder).save()
            # TODO: Make redirect to last page
            return redirect('root_page')
        else:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                ))
    elif request.method == 'GET':
        form = forms.CreateFolderForm()
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
        file_id = request.GET.get('file')

        validate_id_status = validators.validate_file_id(file_id)
        validate_file_exist_status = validators.validate_exist_file(
            request.user,
            file_id
        )
        validate_params_status = validators.validate_get_params(dict(request.GET))
        validate_permission_status = validators.validate_file_permission(
            request.user,
            file_id
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

        if not validate_id_status or not validate_params_status:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                ))

        download_url = s3.get_url(file_id)

        return redirect(download_url)
    else:
        return http.HttpResponseNotAllowed(['GET'])


@login_required(login_url='/login/')
def delete_file(request):
    """View for delete file."""
    if request.method == 'GET':
        file_id = request.GET.get('file')

        validate_id_status = validators.validate_file_id(file_id)
        validate_file_exist_status = validators.validate_exist_file(
            request.user,
            file_id
        )
        validate_params_status = validators.validate_get_params(dict(request.GET))
        validate_permission_status = validators.validate_file_permission(
            request.user,
            file_id
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

        if not validate_id_status or not validate_params_status:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                ))

        if s3.delete_key(request.user, file_id):
            queries.delete_file(file_id)
            return redirect(request.META.get('HTTP_REFERER'))
        else:
            return http.HttpResponse('Cannot delete this file or this file'
                                     'doesn`t exist')

    else:
        return http.HttpResponseNotAllowed(['GET'])


@login_required(login_url='/login/')
def delete_folder(request):
    """Delete folder with all files inside."""
    if request.method == 'GET':
        folder_id = request.GET.get('folder')
        id_status = validators.validate_id_for_folder(folder_id)

        params_status = validators.validate_get_params(
            dict(request.GET))
        folder_id_status = validators.validate_folder_id(folder_id)
        folder_exist_status = validators.validate_parent_folder(folder_id)
        folder_permission_status = validators.validate_folder_permission(
            request.user,
            folder_id
        )

        if not folder_permission_status:
            return http.HttpResponseForbidden(
                content=render(
                    request=request,
                    template_name='assets/errors/403_error_page.html'
                ))

        if (not id_status or
                not params_status or
                not folder_exist_status or
                not params_status or
                not folder_id_status):
            return http.HttpResponseBadRequest(content=render(
                request=request,
                template_name='assets/errors/400_error_page.html'
            ))

        s3.delete_recursive(folder_id)
        return redirect(request.META.get('HTTP_REFERER'))

    else:
        return http.HttpResponseNotAllowed(['GET'])


@login_required(login_url='/login/')
def move_file(request):
    """View for move file."""
    if request.method == 'POST':
        form = forms.MoveFileForm(request.POST, user=request.user)
        if form.is_valid():
            new_folder_id = request.POST.get('new_folder', None)

            if new_folder_id is None:
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            file_id = request.GET.get('file')

            if new_folder_id == 'None':
                new_folder_id = None

            file_status = validators.validate_file_id(file_id)
            folder_exist_status = validators.validate_parent_folder(new_folder_id)
            file_permission_status = validators.validate_file_permission(
                request.user,
                file_id
            )
            file_exist_status = validators.validate_exist_file(request.user, file_id)
            params_status = validators.validate_get_params(dict(request.GET))

            if new_folder_id is not None:
                folder_permission_status = validators.validate_folder_permission(
                    request.user,
                    new_folder_id
                )
            else:
                folder_permission_status = True

            if not folder_permission_status or not file_permission_status:
                return http.HttpResponseForbidden(
                    content=render(
                        request=request,
                        template_name='assets/errors/403_error_page.html'
                    ))

            if (not file_status or
                    not folder_exist_status or
                    not file_exist_status or
                    not params_status):
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            queries.move_file(new_folder_id, file_id)
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
        form = forms.RenameFileForm(request.POST)
        if form.is_valid():
            new_title = request.POST.get('new_title', None)

            if new_title is None:
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            file_id = request.GET.get('file')
            new_title = new_title.strip()
            file_status = validators.validate_file_id(file_id)
            file_permission_status = validators.validate_file_permission(
                request.user,
                file_id
            )
            file_exist_status = validators.validate_exist_file(request.user, file_id)
            params_status = validators.validate_get_params(dict(request.GET))

            if (not file_exist_status or
                    not file_status or
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

            queries.rename_file(file_id, new_title)
            return redirect('root_page')

        else:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/errors/400_error_page.html'
                ))

    elif request.method == 'GET':
        form = forms.RenameFileForm()
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
            new_title = request.POST.get('new_title', None)

            if new_title is None:
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            folder_id = request.GET.get('folder')
            new_title = new_title.strip()

            folder_id_status = validators.validate_folder_id(folder_id)
            folder_permission_status = validators.validate_folder_permission(
                request.user,
                folder_id
            )
            folder_exist_status = validators.validate_exist_current_folder(
                folder_id)

            params_status = validators.validate_get_params(dict(request.GET))
            new_folder_exist = validators.validate_exist_folder_new_title(
                folder_id,
                new_title,
                request.user
            )

            if new_folder_exist:
                return http.HttpResponse('Cannot rename folder. Check current directory '
                                         'for same title.')

            if (not folder_id_status or
                    not params_status or
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

            queries.rename_folder(folder_id, new_title)
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
                      'assets/rename_file.html',
                      context=context)
    else:
        return http.HttpResponseNotAllowed(['GET', 'POST'])
