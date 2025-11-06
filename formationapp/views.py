from django.shortcuts import render
from .models import Formation
from django.views.generic import ListView
# Create your views here.
class FormationListView(ListView):
    model = Formation
    template_name = 'formationapp/view_formation.html'
    context_object_name = 'formations' 