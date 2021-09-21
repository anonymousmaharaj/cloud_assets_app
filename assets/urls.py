"""Endpoints for Assets application."""

from django.urls import path, include

from assets import views, views_v2

# TODO: Fix upload_file path.

api_urlpatterns = [
    path('assets/folders/', views_v2.FolderListCreate.as_view()),
    path('assets/folder/<int:pk>', views_v2.FolderUpdate.as_view()),
    path('assets/files/', views_v2.FileListCreate.as_view()),
    path('assets/file/<int:pk>', views_v2.FileUpdate.as_view()),
]

urlpatterns = [
    path('api/health_check/', views.health_check),
    path('', views.show_page, name='root_page'),
    path('upload_file/', views.user_upload_file, name='upload_file'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path('download/', views.download_file, name='download_file'),
    path('delete/', views.delete_file, name='delete_file'),
    path('delete-folder/', views.delete_folder, name='delete_folder'),
    path('move/', views.move_file, name='move_file'),
    path('rename-file/', views.rename_file, name='rename_file'),
    path('assets/folder/<int:folder_id>/rename/', views_v2.RenameFolderView.as_view()),
]
