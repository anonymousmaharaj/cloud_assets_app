"""Views for Assets application."""

from assets.db.queries import get_assets_list
from assets.models import Folder

from common.validators import validate_folder_id, validate_get_params

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render


def health_check(request):
    """Response 200 status code."""
    return JsonResponse({'server_status': 200})


def show_page(request):
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

    if folder_id is not None:
        folder_obj = get_object_or_404(Folder, pk=folder_id)

    rows = get_assets_list(folder_id)
    context = {'rows': rows, 'folder_obj': folder_obj}
    return render(request, 'assets/root_page.html', context)
