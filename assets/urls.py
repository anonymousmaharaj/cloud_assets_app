from assets.views import health_check, show_page

from django.urls import path

urlpatterns = [
    path('api/health_check/', health_check),
    path('', show_page, name='root_page'),
    path('?folder=<int:folder_id>', show_page, name='folder_page'),
]
