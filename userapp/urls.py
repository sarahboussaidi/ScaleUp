from django.urls import path  # type: ignore
from django.contrib.auth import views as auth_views # type: ignore
from . import views



urlpatterns = [
    path('signin/', views.signin_view, name='signin'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.update_profile, name='update_profile'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('logout/', views.logout_view, name='logout'),
    path('candidats/', views.candidats_listing, name='candidats_listing'),
    path('candidat/<int:candidat_id>/', views.candidat_detail, name='candidat_detail'),

]
