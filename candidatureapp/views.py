from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Candidature
from .forms import CandidatureForm
from django.db.models import Count

# --- CRUD ---

def liste_candidatures(request):
    candidatures = Candidature.objects.all()
    return render(request, 'candidatureapp/liste.html', {'candidatures': candidatures})

def ajouter_candidature(request):
    if request.method == 'POST':
        form = CandidatureForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Candidature ajoutée avec succès.")
            return redirect('liste_candidatures')
    else:
        form = CandidatureForm()
    return render(request, 'candidatureapp/ajouter.html', {'form': form})

def modifier_candidature(request, id):
    candidature = get_object_or_404(Candidature, pk=id)
    if request.method == 'POST':
        form = CandidatureForm(request.POST, request.FILES, instance=candidature)
        if form.is_valid():
            form.save()
            messages.success(request, "Candidature modifiée avec succès.")
            return redirect('liste_candidatures')
    else:
        form = CandidatureForm(instance=candidature)
    return render(request, 'candidatureapp/modifier.html', {'form': form, 'candidature': candidature})

def supprimer_candidature(request, id):
    candidature = get_object_or_404(Candidature, pk=id)
    candidature.delete()
    messages.success(request, "Candidature supprimée.")
    return redirect('liste_candidatures')

def details_candidature(request, id):
    candidature = get_object_or_404(Candidature, pk=id)
    return render(request, 'candidatureapp/details.html', {'candidature': candidature})

# --- MÉTIERS SIMPLES ---
def stats_par_statut(request):
    stats = Candidature.objects.values('statut').annotate(total=Count('statut'))
    return render(request, 'candidatureapp/stats.html', {'stats': stats})

# --- MÉTIERS AVANCÉS ---
def candidatures_par_candidat(request, id_candidat):
    candidatures = Candidature.objects.filter(id_candidat_id=id_candidat)
    return render(request, 'candidatureapp/par_candidat.html', {'candidatures': candidatures})

# --- IA (analyse simple d’une lettre de motivation) ---
def analyse_ia(request, id):
    candidature = get_object_or_404(Candidature, pk=id)
    texte = candidature.lettre_motivation or ""
    score = len(texte.split())  # analyse simple : compte de mots
    niveau = "Bonne" if score > 100 else "Faible"
    return render(request, 'candidatureapp/ia.html', {
        'candidature': candidature,
        'score': score,
        'niveau': niveau
    })
