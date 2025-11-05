from django.urls import path
from . import views

urlpatterns = [
    path('', views.liste_candidatures, name='liste_candidatures'),
    path('ajouter/', views.ajouter_candidature, name='ajouter_candidature'),
    path('modifier/<int:id>/', views.modifier_candidature, name='modifier_candidature'),
    path('supprimer/<int:id>/', views.supprimer_candidature, name='supprimer_candidature'),
    path('details/<int:id>/', views.details_candidature, name='details_candidature'),
]
