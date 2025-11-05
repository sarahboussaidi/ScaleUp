from django.urls import path
from . import views
urlpatterns = [
    path('list/', views.list_freelances, name='list'),
]