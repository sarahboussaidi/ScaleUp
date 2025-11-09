from django.urls import path
from . import views
urlpatterns = [
    path('list/', views.list_freelances, name='list'),
    path('grid/', views.freelance_grid_2, name='freelance_grid_2'),
    path('add/', views.add_freelance, name='add_freelance'),
    path('update/<int:id>/', views.update_freelance, name='update_freelance'),
    path('delete/<int:id>/', views.delete_freelance, name='delete_freelance'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),
]