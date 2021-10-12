"""Views for authentication."""

from authentication import forms
from django import http
from django.contrib import auth
from django.contrib import messages
from django.shortcuts import redirect, render


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
    return render(request, 'authentication/login.html', context)


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
            return redirect('login')
        else:
            messages.error(request, 'Error!')
            return render(request, 'authentication/register.html', context={'form': form})

    elif request.method == 'GET':
        form = forms.UserRegisterForm()
        context = {'form': form}
        return render(request,
                      'authentication/register.html',
                      context=context)
    else:
        return http.HttpResponseNotAllowed(['GET', 'POST'])
