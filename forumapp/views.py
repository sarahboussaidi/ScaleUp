from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from .models import *
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.core.paginator import Paginator
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Create your views here.

class SujetForm(forms.ModelForm):
    titre = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'required': True, 'maxlength': 200}),
        label='Titre'
    )
    description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'required': True, 'maxlength': 2000}),
        label='Description'
    )

    class Meta:
        model = Sujet
        fields = ['titre', 'description']

    def clean_titre(self):
        titre = (self.cleaned_data.get('titre') or '').strip()
        if not titre:
            raise forms.ValidationError('Le titre est requis.')
        if len(titre) < 3:
            raise forms.ValidationError('Le titre est trop court (au moins 3 caractères).')
        # check for duplicate titles (case-insensitive). exclude current instance when editing.
        qs = Sujet.objects.filter(titre__iexact=titre)
        if getattr(self, 'instance', None) and getattr(self.instance, 'pk', None):
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Un sujet avec ce titre existe déjà.')
        return titre

    def clean_description(self):
        desc = (self.cleaned_data.get('description') or '').strip()
        if not desc:
            raise forms.ValidationError('La description est requise.')
        if len(desc) < 10:
            raise forms.ValidationError('La description est trop courte (au moins 10 caractères).')
        return desc


class QuestionForm(forms.ModelForm):
    texte = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'required': True, 'maxlength': 1000}),
        label='Question'
    )

    class Meta:
        model = Question
        # don't expose 'utilisateur' or 'date_creation' in the form; we'll set them server-side
        fields = ['texte', 'sujet']

    def clean_texte(self):
        texte = (self.cleaned_data.get('texte') or '').strip()
        if not texte:
            raise forms.ValidationError('Le texte de la question est requis.')
        if len(texte) < 5:
            raise forms.ValidationError('La question est trop courte (au moins 5 caractères).')
        return texte


class ReponseForm(forms.ModelForm):
    texte = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'required': True, 'maxlength': 1000}),
        label='Réponse'
    )

    class Meta:
        model = Reponse
        fields = ['texte', 'question']

    def clean_texte(self):
        texte = (self.cleaned_data.get('texte') or '').strip()
        if not texte:
            raise forms.ValidationError('Le texte de la réponse est requis.')
        if len(texte) < 2:
            raise forms.ValidationError('La réponse est trop courte (au moins 2 caractères).')
        return texte


class AddSujetView(LoginRequiredMixin, CreateView):
    model = Sujet
    form_class = SujetForm
    template_name = 'forumapp/sujet_form.html'
    success_url = '/forum/sujets/'

    def form_valid(self, form):
        # set the author to the currently logged-in user before saving
        form.instance.author = self.request.user
        return super().form_valid(form)

class UpdateSujetView(LoginRequiredMixin, UpdateView):
    model = Sujet
    form_class = SujetForm
    template_name = 'forumapp/sujet_form.html'
    success_url = '/forum/sujets/'

    def get_queryset(self):
        # restrict updates to sujets owned by the current user
        return Sujet.objects.filter(author=self.request.user)

class DeleteSujetView(LoginRequiredMixin, DeleteView):
    model = Sujet
    template_name = 'forumapp/sujet_confirm_delete.html'
    success_url = '/forum/sujets/'

    def get_queryset(self):
        # restrict deletes to sujets owned by the current user
        return Sujet.objects.filter(author=self.request.user)

class AddQuestionView(LoginRequiredMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'forumapp/view_sujet.html'

    def get_success_url(self):
        return reverse('view_sujet', kwargs={'sujet_id': self.object.sujet.pk})

    def form_valid(self, form):
        # attach the current user as the author, save, then redirect to the sujet detail
        form.instance.utilisateur = self.request.user
        self.object = form.save()
        return redirect('view_sujet', sujet_id=self.object.sujet.pk)

class QuestionFormView(CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'forumapp/view_sujet.html'

    def form_valid(self, form):
        # save the object and redirect to the related sujet view to avoid relying on self.object
        self.object = form.save()
        return redirect('view_sujet', sujet_id=self.object.sujet.pk)

def view_sujet(request, sujet_id):
    sujet = get_object_or_404(Sujet, pk=sujet_id)
    questions = Question.objects.filter(sujet=sujet)
    reponses = Reponse.objects.filter(question__in=questions)
    # provide a QuestionForm so the modal (or direct AddQuestionView using this template)
    # can render the form fields. The form includes the 'sujet' field, so prefill it.
    try:
        form = QuestionForm(initial={'sujet': sujet})
    except NameError:
        # if QuestionForm isn't available in this namespace for some reason,
        # fall back to None so templates can handle it.
        form = None

    return render(request, 'forumapp/view_sujet.html', {
        'sujet': sujet,
        'questions': questions,
        'reponses': reponses,
        'form': form,
    })

def list_sujets(request):
    # paginate sujets: 5 per page
    sujets_qs = Sujet.objects.all().order_by('-date_creation')
    paginator = Paginator(sujets_qs, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    sujets = page_obj  # Page is iterable in templates

    # include the 5 most recently created sujets for the sidebar
    latest_sujets = list(Sujet.objects.order_by('-date_creation')[:5])

    # small set of fallback images to pick randomly from
    fallback_images = [
        '/static/imgs/blog/thumb-1.png',
        '/static/imgs/blog/thumb-2.png',
        '/static/imgs/blog/thumb-3.png',
        '/static/imgs/blog/thumb-4.png',
        '/static/imgs/blog/thumb-5.png',
    ]

    # removed thumb_url assignment — templates will use the Sujet.image field with a fallback

    return render(request, 'forumapp/list_sujets.html', {
        'sujets': sujets,
        'latest_sujets': latest_sujets,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
    })


@login_required
def user_sujets(request):
    """Show only the sujets created by the authenticated user."""
    user = request.user
    sujets = list(Sujet.objects.filter(author=user))

    # reuse the same random thumbnail logic used in list_sujets
    fallback_images = [
        '/static/imgs/blog/thumb-1.png',
        '/static/imgs/blog/thumb-2.png',
        '/static/imgs/blog/thumb-3.png',
        '/static/imgs/blog/thumb-4.png',
        '/static/imgs/blog/thumb-5.png',
    ]
    # removed thumb_url assignment — templates will use the Sujet.image field with a fallback

    return render(request, 'Forumapp/user_sujet.html', {'sujets': sujets})


@login_required
def add_reponse(request):
    """Handle POST to create a Reponse and redirect back to the parent sujet.

    Expects POST fields: 'question' (id) and 'texte'.
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST allowed')

    # Prefer using the ReponseForm so server-side validation runs consistently
    form = ReponseForm(request.POST)
    if not form.is_valid():
        # return JSON errors so frontend can handle them; using BadRequest to keep previous behavior
        return HttpResponseBadRequest(form.errors.as_json(), content_type='application/json')

    reponse = form.save(commit=False)
    reponse.utilisateur = request.user
    reponse.save()
    # ensure we have the related question available for broadcasting/redirect
    question = reponse.question

    # Broadcast the new response to any WebSocket clients listening on the question group
    try:
        channel_layer = get_channel_layer()
        payload = {
            'id': reponse.id,
            'texte': reponse.texte,
            'utilisateur': reponse.utilisateur.username,
            'date_creation': reponse.date_creation.isoformat(),
            'question_id': question.id,
        }
        async_to_sync(channel_layer.group_send)(
            f'question_{question.id}',
            {
                'type': 'new_response',
                'payload': payload,
            }
        )
    except Exception:
        # If channels isn't available or channel layer not configured, ignore broadcasting
        pass

    return redirect('view_sujet', sujet_id=question.sujet.pk)

class UpdateQuestionView(UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'forumapp/view_sujet.html'

    def get_success_url(self):
        return reverse('view_sujet', kwargs={'sujet_id': self.object.sujet.pk})
    
class DeleteQuestionView(DeleteView):
    model = Question
    template_name = 'forumapp/question_confirm_delete.html'

    def get_success_url(self):
        return reverse('view_sujet', kwargs={'sujet_id': self.object.sujet.pk})
    
class UpdateReponseView(UpdateView):
    model = Reponse
    form_class = ReponseForm
    template_name = 'forumapp/view_sujet.html'

    def get_success_url(self):
        return reverse('view_sujet', kwargs={'sujet_id': self.object.question.sujet.pk})    

class DeleteReponseView(DeleteView):
    model = Reponse
    template_name = 'forumapp/reponse_confirm_delete.html'

    def get_success_url(self):
        return reverse('view_sujet', kwargs={'sujet_id': self.object.question.sujet.pk})