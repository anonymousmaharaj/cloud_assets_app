"""Endpoints for Assets application."""

from django.urls import path

from assets import views, views_v2

# TODO: Fix upload_file path.

api_urlpatterns = [
    path('assets/folders/', views_v2.FolderListCreateView.as_view(), name='assets-api-folders'),
    path('assets/folders/<int:pk>/', views_v2.FolderRetrieveUpdateView.as_view()),
    path('assets/files/', views_v2.FileListCreateView.as_view()),
    path('assets/files/<int:pk>/', views_v2.FileRetrieveUpdateDestroyView.as_view()),
    path('assets/files/share', views_v2.ShareFileListCreateView.as_view()),
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
    path('assets/files/<int:file_id>/share/', views_v2.CreateShareView.as_view()),
    path('assets/files/shared/', views_v2.ListShareView.as_view(), name='share-list'),
    path('assets/files/shared/<int:share_id>/update/', views_v2.UpdateShareView.as_view()),
    path('assets/files/shared/<int:share_id>/delete/', views_v2.DeleteShareView.as_view()),
    path('assets/files/<int:file_id>/share/download/', views_v2.DownloadShareFileView.as_view()),
    path('assets/files/<int:file_id>/share/rename/', views_v2.RenameShareFileView.as_view()),
    path('assets/files/<int:file_id>/share/delete/', views_v2.DeleteShareFileView.as_view()),
]
