from assets.models import File, Folder

from django.http import JsonResponse
from django.shortcuts import render


def health_check(request):
    return JsonResponse({'server_status': 200})


def root_page(request):
    # TODO: Re-implement with raw SQL
    files = File.objects.filter(folder_id=None)
    folders = Folder.objects.filter(parent_id=None)
    context = {'files': files, 'folders': folders}
    return render(request, 'assets/root_page.html', context)


def folder_page(request, folder_id):
    files = File.objects.filter(folder_id=folder_id)
    current_folder = Folder.objects.get(pk=folder_id)
    folders = Folder.objects.filter(parent_id=folder_id)
    context = {'files': files,
               'folders': folders,
               'current_folder': current_folder
               }
    return render(request, 'assets/folder_page.html', context)
