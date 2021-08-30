"""Views for Assets application."""
import os

from assets.db.queries import get_assets_list
from assets.forms import UploadFileForm, UserLoginForm, UserRegisterForm
from assets.models import File, Folder
from assets.utils.s3 import upload_file
from assets.utils.validators import validate_upload_file

from common.validators import validate_folder_id, validate_get_params

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render


def health_check(request):
    """Response 200 status code."""
    return JsonResponse({'server_status': 200})


@login_required(login_url='/login/')
def show_page(request):
    """Render page for display assets."""
    folder_id = request.GET.get('folder')

    validate_id_status = validate_folder_id(folder_id)
    validate_params_status = validate_get_params(dict(request.GET))

    if not validate_id_status == 200:
        return validate_id_status(content=render(
            request=request,
            template_name='assets/400_error_page.html'
        ))

    if not validate_params_status == 200:
        return validate_params_status(content=render(
            request=request,
            template_name='assets/400_error_page.html'
        ))

    folder_obj = get_object_or_404(Folder, pk=folder_id) if folder_id else None

    rows = get_assets_list(folder_id)
    context = {'rows': rows, 'folder_obj': folder_obj}
    return render(request, 'assets/root_page.html', context)


@login_required(login_url='/login/')
def user_upload_file(request):
    """Upload file to S3.

    Render form. Get file's path and upload it on S3.
    Create new object in File table.
    """
    if request.method == 'POST':
        form = UploadFileForm(request.POST)
        if form.is_valid():
            upload_path = request.POST.get('path')
            validate_status = validate_upload_file(upload_path)
            if validate_status is False:
                return HttpResponse(f'No such file in directory {upload_path}')
            if upload_file(upload_path, 'django-cloud-assets'):
                File.create_file(
                    title=os.path.basename(upload_path),
                    owner=request.user)
                return HttpResponse('Your file will be downloaded')
            else:
                return HttpResponse('Error')
    elif request.method == 'GET':
        form = UploadFileForm()
        return render(request, 'assets/upload_file.html', {'form': form})
    else:
        return HttpResponseNotAllowed()


def user_login(request):
    """View for user login."""
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('root_page')
    else:
        form = UserLoginForm()
    context = {'form': form}
    return render(request, 'assets/login.html', context)


def user_logout(request):
    """View for user logout."""
    logout(request)
    return redirect('login')


def user_register(request):
    """View for register."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Success!')
            return redirect('root_page')
        else:
            messages.error(request, 'Error!')
    else:
        form = UserRegisterForm()
    context = {'form': form}
    return render(request, 'assets/register.html', context=context)
