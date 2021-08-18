from django.urls import path
from clouds.views import health_check

urlpatterns = [
    path('api/health_check/', health_check)
]