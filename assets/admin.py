from assets.models import File, Folder

from django.contrib import admin


# Register your models here.

class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'folder_id')
    fields = ('title', 'folder_id')


class FolderAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'parent_id')
    fields = ('title', 'parent_id')


admin.site.register(File, FileAdmin)
admin.site.register(Folder, FolderAdmin)
