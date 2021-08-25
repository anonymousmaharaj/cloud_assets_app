from assets.views import health_check, show_page, user_login, user_logout

from django.urls import path

urlpatterns = [
    path('api/health_check/', health_check),
    path('', show_page, name='root_page'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout')
]
