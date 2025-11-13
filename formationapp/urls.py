from django.urls import path
from .views import *

urlpatterns = [
    path('view_formation',FormationListView.as_view(), name='view_formation'),
    path('formation_admin',FormationList.as_view(), name='formation_admin'),
    path('formationcreate/',FormationCreateView.as_view(),name='formation_create'),
    path('delete/<int:pk>/',FormationDeleteView.as_view(),name='formation_delete'),
    path('update/<int:pk>/',FormationUpdateView.as_view(),name='formation_update'),
]