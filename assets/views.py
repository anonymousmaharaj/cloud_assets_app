from assets.db.queries import get_assets_list

from django.http import JsonResponse
from django.shortcuts import render


def health_check(request):
    return JsonResponse({'server_status': 200})


def show_page(request):
    rows = get_assets_list(None)
    context = {'rows': rows}
    return render(request, 'assets/root_page.html', context)
