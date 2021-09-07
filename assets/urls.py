"""Endpoints for Assets application."""

from django.urls import path

from assets import views

# TODO: Fix upload_file path.
urlpatterns = [
    path('api/health_check/', views.health_check),
    path('', views.show_page, name='root_page'),
    path('upload_file/', views.user_upload_file, name='upload_file'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('create-folder/', views.create_folder, name='create_folder'),
    path('download/', views.download_file, name='download_file'),
    path('delete/', views.delete_file, name='delete_file'),
    path('delete-folder/', views.delete_folder, name='delete_folder'),
    path('move/', views.move_file, name='move_file'),
    path('rename-file/', views.rename_file, name='rename_file')
]
