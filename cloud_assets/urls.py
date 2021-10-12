"""cloud_assets URL Configuration."""

from django.contrib import admin
from django.urls import include, path
from cloud_assets import settings
from cloud_assets.yasg import urlpatterns as swagger_urlpatterns

from assets import urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('assets.urls')),
    path('', include('authentication.urls')),
    path('api/', include(urls.api_urlpatterns))
]
if settings.DEBUG:
    urlpatterns += swagger_urlpatterns
