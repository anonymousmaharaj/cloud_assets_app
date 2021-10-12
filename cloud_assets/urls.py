"""cloud_assets URL Configuration."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static

from assets import urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('assets.urls')),
    path('', include('authentication.urls')),
    path('api/', include(urls.api_urlpatterns))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
