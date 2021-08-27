"""Views for Assets application."""

from assets.db.queries import get_assets_list

from assets.forms import UserLoginForm, UserRegisterForm
from assets.models import Folder

from django.contrib import messages
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from common.validators import validate_folder_id, validate_get_params



def health_check(request):
    """Response 200 status code."""
    return JsonResponse({'server_status': 200})


def show_page(request):
    """Render page for display assets."""
    folder_obj = None
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

    # TODO: Fix this check
    if folder_id is not None:
        folder_obj = get_object_or_404(Folder, pk=folder_id)

    rows = get_assets_list(folder_id)
    context = {'rows': rows, 'folder_obj': folder_obj}
    return render(request, 'assets/root_page.html', context)


def user_login(request):
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
    logout(request)
    return redirect('login')


def user_register(request):
    """Register new user."""
    # TODO: Protect cases with other type's of methods.
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