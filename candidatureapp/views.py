from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Candidature
from .forms import CandidatureForm
from django.db.models import Count
from userapp.models import Utilisateur
from stageapp.models import Stage
from freelanceapp.models import Freelance
from formationapp.models import Formation

def modifier_candidature(request, id):
    candidature = get_object_or_404(Candidature, pk=id)

    if request.method == 'POST':
        statut = request.POST.get('statut')
        lettre = request.POST.get('lettre_motivation')
        cv = request.FILES.get('cv_joint')
        if not statut:
            messages.error(request, "Veuillez sélectionner un statut.")
        elif not lettre or lettre.strip() == "":
            messages.error(request, "Veuillez saisir une lettre de motivation.")
        elif cv and not cv.name.lower().endswith(('.pdf', '.doc', '.docx')):
            messages.error(request, "Le CV doit être un fichier PDF ou Word (.pdf, .doc, .docx).")
        else:
            # ✅ Mise à jour de la candidature
            candidature.statut = statut
            candidature.lettre_motivation = lettre

            # Met à jour le CV uniquement si un nouveau fichier est envoyé
            if cv:
                candidature.cv_joint = cv

            candidature.save()
            messages.success(request, "✅ Candidature modifiée avec succès !")
            return redirect('liste_candidatures')

    return render(request, 'candidature_modifier.html', {'candidature': candidature})


def liste_candidatures(request):
    candidatures = Candidature.objects.all().order_by('-date_candidature')
    return render(request, 'candidature.html', {'candidatures': candidatures})


    
   
def consulter_candidatures(request):
    candidatures = Candidature.objects.select_related(
        'id_candidat', 'id_stage', 'id_freelance', 'id_formation'
    ).all()
    return render(request, 'candidature_consulter.html', {'candidatures': candidatures})

def ajouter_candidature(request):
    utilisateurs = Utilisateur.objects.all()
    stages = Stage.objects.all()
    freelances = Freelance.objects.all()
    formations = Formation.objects.all()

    if request.method == "POST":
        id_candidat = request.POST.get("id_candidat")
        type_cand = request.POST.get("type")
        lettre = request.POST.get("lettre_motivation")
        cv = request.FILES.get("cv_joint")
        if not id_candidat:
            messages.error(request, "Veuillez sélectionner un candidat.")
        elif not type_cand:
            messages.error(request, "Veuillez sélectionner le type de candidature (stage, formation, freelance...).")
        elif not cv:
            messages.error(request, "Veuillez joindre un fichier CV.")
        elif not lettre or lettre.strip() == "":
            messages.error(request, "Veuillez rédiger une lettre de motivation.")
        else:
            # ✅ Si tout est valide → création de la candidature
            candidature = Candidature.objects.create(
                id_candidat_id=id_candidat,
                lettre_motivation=lettre,
                cv_joint=cv,
            )

            if type_cand == "stage":
                candidature.id_stage_id = request.POST.get("id_stage")
            elif type_cand == "freelance":
                candidature.id_freelance_id = request.POST.get("id_freelance")
            elif type_cand == "formation":
                candidature.id_formation_id = request.POST.get("id_formation")

            candidature.save()
            messages.success(request, "✅ Candidature ajoutée avec succès !")
            return redirect('liste_candidatures')

    # Si GET ou erreur de saisie → on recharge la page avec les messages
    return render(request, 'candidature_ajouter.html', {
        'utilisateurs': utilisateurs,
        'stages': stages,
        'freelances': freelances,
        'formations': formations,
    })


def supprimer_candidature(request, id):
    candidature = get_object_or_404(Candidature, id_candidature=id)

    if request.method == 'POST':
        candidature.delete()
        messages.success(request, 'La candidature a été supprimée avec succès.')
    else:
        messages.error(request, 'Méthode non autorisée.')

    return redirect('liste_candidatures')

def details_candidature(request, id):
    candidature = get_object_or_404(Candidature, id_candidature=id)
    return render(request, 'details_candidature.html', {'candidature': candidature})

def login_view(request):
    return render(request, 'login.html')

def register_view(request):
    return render(request, 'register.html')