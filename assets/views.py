"""Views for Assets application."""

from assets.db.queries import get_assets_list

from django.http import JsonResponse
from django.shortcuts import render


def health_check(request):
    """Response 200 status code."""
    return JsonResponse({'server_status': 200})


def show_page(request):
    """Response with all assets from root page."""
    rows = get_assets_list(None)
    context = {'rows': rows}
    return render(request, 'assets/root_page.html', context)
