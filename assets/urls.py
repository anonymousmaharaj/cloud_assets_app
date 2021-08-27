"""Endpoints for Assets application."""

from assets.views import health_check, show_page, user_login, user_logout, user_register

from django.urls import path


urlpatterns = [
    path('api/health_check/', health_check),
    path('', show_page, name='root_page'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout')
    path('register/', user_register, name='register')
]
