from django.urls import path
from .views import *

urlpatterns = [
    path('view_formation',FormationListView.as_view(), name='view_formation'),
]