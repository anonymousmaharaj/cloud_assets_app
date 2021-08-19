from assets.views import folder_page, health_check, root_page

from django.urls import path

urlpatterns = [
    path('api/health_check/', health_check),
    path('', root_page, name='root_page'),
    path('folder/<int:folder_id>', folder_page, name='folder_page'),
]
