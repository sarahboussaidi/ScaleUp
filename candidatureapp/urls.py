from django.urls import path
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('consulter/', views.consulter_candidatures, name='consulter_candidatures'),
    path('ajouter/', views.ajouter_candidature, name='ajouter_candidature'),
    path('liste/', views.liste_candidatures, name='liste_candidatures'),
    path('details/<int:id>/', views.details_candidature, name='details_candidature'),
    path('modifier/<int:id>/', views.modifier_candidature, name='modifier_candidature'),
    path('supprimer/<int:id>/', views.supprimer_candidature, name='supprimer_candidature'),
    path('register/', views.register_view, name='register'),
    path('confirmer_suppression/<int:id>/', views.supprimer_candidature, name='confirmer_suppression'),
    path('/cvs/', views.serve_cv, name='serve_cv'),
    
]
