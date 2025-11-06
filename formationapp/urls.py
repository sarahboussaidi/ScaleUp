from django.urls import path
from .views import *

urlpatterns = [
    path('job-grid-2',FormationListView.as_view(), name='job-grid-2'),
]