from assets.views import health_check, show_page, user_register

from django.urls import path


urlpatterns = [
    path('api/health_check/', health_check),
    path('', show_page, name='root_page'),
    path('register/', user_register, name='register')
]
