from assets.db.queries import get_assets_list
from assets.forms import UserLoginForm

from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.shortcuts import redirect, render


def health_check(request):
    return JsonResponse({'server_status': 200})


def show_page(request):
    rows = get_assets_list(None)
    context = {'rows': rows}
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
