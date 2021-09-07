"""Views for Assets application."""
import os

from django import http
from django.contrib import auth
from django.contrib import messages
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

            parent_folder = models.Folder.objects.filter(
                pk=parent_folder)

            if len(parent_folder) < 1:
                parent_folder = None
            else:
                parent_folder = parent_folder[0]

            if s3.upload_file(upload_path, request.user, parent_folder):
                models.File(title=os.path.basename(upload_path),
                            owner=request.user,
                            folder=parent_folder).save()
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


def user_login(request):
    """View for user login."""
    if request.method == 'POST':
        form = forms.UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth.login(request, user)
            return redirect('root_page')
    else:
        form = forms.UserLoginForm()
    context = {'form': form}
    return render(request, 'assets/login.html', context)


def user_logout(request):
    """View for user logout."""
    auth.logout(request)
    return redirect('login')


def user_register(request):
    """View for register."""
    if request.method == 'POST':
        form = forms.UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Success!')
            return redirect('root_page')
        else:
            messages.error(request, 'Error!')
    elif request.method == 'GET':
        form = forms.UserRegisterForm()
        context = {'form': form}
        return render(request,
                      'assets/register.html',
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
            new_folder_title = request.POST.get('title')
            new_folder_title = new_folder_title.strip()

            if parent_folder == '':
                parent_folder = None

            id_status = validators.validate_id_for_folder(
                parent_folder)
            params_status = validators.validate_get_params(
                dict(request.GET))
            name_status = validators.validate_new_folder_name(
                new_folder_title)
            folder_exist_status = validators.validate_parent_folder(
                parent_folder)
            title_exist_status = validators.validate_exist_folder(
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
            file_id)
        validate_params_status = validators.validate_get_params(
            dict(request.GET))
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

        download_url = s3.get_url(request.user, file_id)

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
            file_id)
        validate_params_status = validators.validate_get_params(
            dict(request.GET))
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

        if s3.delete_file(request.user, file_id):
            models.File.objects.get(pk=file_id).delete()
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
        folder_exist_status = validators.validate_parent_folder(
            folder_id)
        folder_permission_status = validators.validate_folder_permission(
            request.user,
            folder_id)

        if not folder_permission_status:
            return http.HttpResponseForbidden(
                content=render(
                    request=request,
                    template_name='assets/errors/403_error_page.html'
                ))

        if (not id_status or
                not params_status or
                not folder_exist_status):
            return http.HttpResponseBadRequest(content=render(
                request=request,
                template_name='assets/errors/400_error_page.html'
            ))

        if s3.delete_folders(request.user, folder_id):
            queries.delete_recursive(folder_id)
            return redirect(request.META.get('HTTP_REFERER'))
        else:
            return http.HttpResponse('Cannot delete this folder.')

    else:
        return http.HttpResponseNotAllowed(['GET'])


def move_file(request):
    """View for move file."""
    if request.method == 'POST':
        form = forms.MoveFileForm(request.POST, user=request.user)
        if form.is_valid():
            new_folder_id = request.POST.get('new_folder')
            file_id = request.GET.get('file')

            if new_folder_id == 'None':
                new_folder_id = None

            file_status = validators.validate_file_id(file_id)
            folder_exist_status = validators.validate_parent_folder(
                new_folder_id)
            file_permission_status = validators.validate_file_permission(
                request.user,
                file_id
            )
            file_exist_status = validators.validate_exist_file(request.user, file_id)

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
                    not file_exist_status):
                return http.HttpResponseBadRequest(
                    content=render(
                        request=request,
                        template_name='assets/errors/400_error_page.html'
                    ))

            if s3.move_file(request.user, new_folder_id, file_id):
                queries.move_file(request.user, new_folder_id, file_id)
                return redirect('root_page')
            else:
                return http.HttpResponse('Cannot move this folder. '
                                         'Or this file already exist in '
                                         'target directory.')

    elif request.method == 'GET':
        form = forms.MoveFileForm(user=request.user)
        context = {'form': form}
        return render(request,
                      'assets/move_file.html',
                      context=context)
    else:
        return http.HttpResponseNotAllowed(['GET', 'POST'])
