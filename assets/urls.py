from assets.views import health_check

from django.urls import path

urlpatterns = [
    path('api/health_check/', health_check)
]
