#from django.shortcuts import render
from .models import Formation, lesson
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DeleteView, UpdateView, DetailView
from .forms import FormationForm, LessonForm
from django.shortcuts import redirect

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
    success_url=reverse_lazy('formation_admin')
    def form_valid(self, form):
        # set the author to the currently authenticated user by default
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            form.instance.author = self.request.user
        return super().form_valid(form)

class FormationDeleteView(DeleteView):
    model = Formation
    fields = "__all__"
    success_url=reverse_lazy('formation_admin')

class FormationUpdateView(UpdateView):
    model = Formation
    #fields = "__all__"
    form_class = FormationForm
    success_url=reverse_lazy('formation_admin')

#----------------lessons views----------------
class FormationDetailView(DetailView):
    model = Formation
    template_name = 'formationapp/formation_detail.html'
    context_object_name = 'formation'
    pk_url_kwarg = 'id_formation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lessons'] = self.object.lessons.all().order_by('-created_at')
        return context
class FormationDetail(DetailView):
    model = Formation
    template_name = 'formationapp/formation_detail_admin.html'
    context_object_name = 'formation'
    pk_url_kwarg = 'id_formation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lessons'] = self.object.lessons.all().order_by('-created_at')
        return context
class LessonCreateView(CreateView):
    model = lesson
    form_class = LessonForm
    template_name = 'formationapp/lesson_form.html'
    
    def form_valid(self, form):
        # Get the formation ID from the URL
        formation_id = self.kwargs['id_formation']
        form.instance.formation_id = formation_id
        return super().form_valid(form)
    
    def get_success_url(self):
        formation_id = self.kwargs['id_formation']
        return reverse_lazy('formation_detail_admin', kwargs={'id_formation': formation_id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formation'] = Formation.objects.get(id_formation=self.kwargs['id_formation'])
        return context
class LessonUpdateView(UpdateView):
    model = lesson
    form_class = LessonForm
    template_name = 'formationapp/lesson_form.html'
    pk_url_kwarg = 'id_lesson'
    
    def get_success_url(self):
        return reverse_lazy('formation_detail_admin', kwargs={'id_formation': self.object.formation.id_formation})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formation'] = self.object.formation
        context['is_update'] = True  # Flag to differentiate between create and update
        return context
class LessonDeleteView(DeleteView):
    model = lesson
    pk_url_kwarg = 'id_lesson'  # tell Django which URL parameter is the PK
    context_object_name = 'lesson'

    def get_success_url(self):
        return reverse_lazy(
            'formation_detail_admin',
            kwargs={'id_formation': self.object.formation.id_formation}
        )

