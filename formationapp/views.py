#from django.shortcuts import render
from .models import Formation
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, UpdateView
from .forms import FormationForm
# Create your views here.
class FormationListView(ListView):
    model = Formation
    template_name = 'formationapp/view_formation.html'
    context_object_name = 'formations' 

class FormationList(ListView):
    model = Formation
    template_name = 'formationapp/formation_admin.html'
    context_object_name = 'formations'

class FormationCreateView(CreateView):
    model = Formation
    #fields = "__all__"
    form_class = FormationForm
    success_url=reverse_lazy('view_formation')

class FormationDeleteView(DeleteView):
    model = Formation
    fields = "__all__"
    success_url=reverse_lazy('formation_admin')

class FormationUpdateView(UpdateView):
    model = Formation
    #fields = "__all__"
    form_class = FormationForm
    success_url=reverse_lazy('formation_admin')