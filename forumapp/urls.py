from django.contrib import admin
from django.urls import path, include
from .views import * 

urlpatterns = [
    path('sujets/', list_sujets, name='list_sujets'),
    path('sujets/<int:sujet_id>/', view_sujet, name='view_sujet'),
    path('sujets/ajouter/', AddSujetView.as_view(), name='add_sujet'),
    path('mes-sujets/', user_sujets, name='user_sujets'),
    path('sujets/<int:pk>/modifier/', UpdateSujetView.as_view(), name='update_sujet'),
    path('sujets/<int:pk>/supprimer/', DeleteSujetView.as_view(), name='delete_sujet'),
    path('questions/ajouter/', AddQuestionView.as_view(), name='add_question'),
    path('reponses/ajouter/', add_reponse, name='add_reponse'),
    path('sujets/<int:sujet_id>/questions/<int:pk>/modifier/', UpdateQuestionView.as_view(), name='update_question'),
    path('questions/<int:pk>/supprimer/', DeleteQuestionView.as_view(), name='delete_question'),
    path('reponses/<int:pk>/modifier/', UpdateReponseView.as_view(), name='update_reponse'),
    path('reponses/<int:pk>/supprimer/', DeleteReponseView.as_view(), name='delete_reponse'),
    ]
