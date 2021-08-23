from assets.db.queries import get_assets_list
from common.validators import validate_int
from .models import Folder

from django.http import JsonResponse
from django.shortcuts import render


def health_check(request):
    return JsonResponse({'server_status': 200})


def show_page(request):
    folder_id = request.GET.get('folder', None)
    if folder_id is not None:
        folder_id = validate_int(folder_id)
    rows = get_assets_list(folder_id)
    if folder_id is not None:
        folder_obj = Folder.objects.get(pk=folder_id)
        context = {'rows': rows, 'folder_obj': folder_obj}
    else:
        context = {'rows': rows}

    return render(request, 'assets/root_page.html', context)
