"""Views for Assets application."""
import os

from assets.db.queries import get_assets_list
from assets.forms import UploadFileForm
from assets.models import File
from assets.utils.s3 import upload_file
from assets.utils.validators import validate_upload_file

from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
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
                File.create_file(title=os.path.basename(upload_path), owner=request.user)
                return HttpResponse('Your file will be downloaded')
            else:
                return HttpResponse('Error')
    elif request.method == 'GET':
        form = UploadFileForm()
        return render(request, 'assets/upload_file.html', {'form': form})
    else:
        return HttpResponseNotAllowed()
