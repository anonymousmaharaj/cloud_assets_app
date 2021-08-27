"""Views for Assets application."""

from assets.db.queries import get_assets_list
from assets.forms import UploadFileForm
from assets.utils.s3 import upload_file
from assets.utils.validators import validate_upload_file

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render


def health_check(request):
    """Response 200 status code."""
    return JsonResponse({'server_status': 200})


def show_page(request):
    """Response with all assets from root page."""
    rows = get_assets_list(None)
    context = {'rows': rows}
    return render(request, 'assets/root_page.html', context)


def user_upload_file(request):
    """Render form. Get file's path and upload it on S3."""
    if request.method == 'POST':
        form = UploadFileForm(request.POST)
        if form.is_valid():
            upload_path = request.POST.get('path')
            validate_status = validate_upload_file(upload_path)
            if validate_status is False:
                return HttpResponse(f'No such file in directory {upload_path}')
            if upload_file(upload_path, 'django-cloud-assets'):
                return HttpResponse('Your file will be downloaded')
            else:
                return HttpResponse('Error')
    else:
        form = UploadFileForm()
    return render(request, 'assets/upload_file.html', {'form': form})
