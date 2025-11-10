from django.urls import path  # type: ignore
from . import views


urlpatterns = [
    path('signin/', views.signin_view, name='signin'),
    path('register/', views.register_view, name='register'),
]
