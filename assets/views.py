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
        return http.HttpResponseBadRequest(content=render(
            request=request,
            template_name='assets/400_error_page.html'
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
            upload_path = request.POST.get('path')
            validate_status = validators.validate_upload_file(upload_path)
            file_exist = validators.validate_exist_file(upload_path,
                                                        user=request.user,
                                                        folder=None)
            if not validate_status:
                return http.HttpResponse(
                    f'No such file in directory {upload_path}')
            if file_exist:
                return http.HttpResponse('File already exist in folder.')

            models.File(title=os.path.basename(upload_path),
                        owner=request.user,
                        folder=None).save()
            if s3.upload_file(upload_path, request.user):
                return http.HttpResponse('Your file is uploaded.')
            else:
                return http.HttpResponse(
                    'Your file already exist in target directory.'
                )
        else:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/400_error_page.html'
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

            if parent_folder == '':
                parent_folder = None

            id_status = validators.validate_id_for_create_folder(
                parent_folder)
            params_status = validators.validate_get_params(
                dict(request.GET))
            name_status = validators.validate_new_folder_name(
                new_folder_title)

            if (not id_status or
                    not params_status or
                    not name_status):
                return http.HttpResponseBadRequest(content=render(
                    request=request,
                    template_name='assets/400_error_page.html'
                ))

            models.Folder(title=new_folder_title,
                          owner=request.user,
                          parent_id=parent_folder).save()
            return redirect('root_page')
        else:
            return http.HttpResponseBadRequest(
                content=render(
                    request=request,
                    template_name='assets/400_error_page.html'
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
