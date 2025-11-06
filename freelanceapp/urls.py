from django.urls import path
from . import views
urlpatterns = [
    path('list/', views.list_freelances, name='list'),
    path('grid/', views.freelance_grid_2, name='freelance_grid_2'),
    path('add/', views.add_freelance, name='add_freelance'),

]