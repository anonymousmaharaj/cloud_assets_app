from assets.db.queries import get_assets_list
from assets.forms import UserRegisterForm

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render


def health_check(request):
    return JsonResponse({'server_status': 200})


def show_page(request):
    rows = get_assets_list(None)
    context = {'rows': rows}
    return render(request, 'assets/root_page.html', context)


def user_register(request):
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
