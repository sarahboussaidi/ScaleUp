from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import Candidature, Utilisateur, Stage, Freelance, Formation

# ------------------------------
# Liste des candidatures
# ------------------------------
def liste_candidatures(request):
    # Show only the candidatures for the currently authenticated user
    if request.user.is_authenticated:
        candidatures = Candidature.objects.filter(id_candidat=request.user)
        # Load related objects to avoid extra queries and ensure related attrs available
        candidatures = candidatures.select_related('id_stage', 'id_formation', 'id_freelance').order_by('-date_candidature')
    else:
        candidatures = Candidature.objects.none()

    return render(request, 'candidatureapp/liste_candidature.html', {'candidatures': candidatures})


# ------------------------------
# Ajouter ou modifier une candidature
# ------------------------------
def form_candidature(request, id=None):
    update = id is not None
    if update:
        candidature = get_object_or_404(Candidature, pk=id)
    else:
        candidature = Candidature()

    utilisateurs = Utilisateur.objects.all()
    stages = Stage.objects.all()
    freelances = Freelance.objects.all()
    formations = Formation.objects.all()

    post_data = request.POST if request.method == "POST" else None
    files_data = request.FILES if request.method == "POST" else None

    if request.method == "POST":
        # Récupération des valeurs du formulaire
        id_candidat = request.POST.get("id_candidat")
        type_cand = request.POST.get("type")
        lettre = request.POST.get("lettre_motivation")
        cv = request.FILES.get("cv_joint")
        statut = request.POST.get("statut") if update else None

        # Validation
        error = False

        if not id_candidat:
            messages.error(request, "Veuillez choisir un candidat.")
            error = True
        if not type_cand:
            messages.error(request, "Veuillez choisir le type.")
            error = True
        if not lettre or lettre.strip() == "":
            messages.error(request, "Veuillez rédiger une lettre de motivation.")
            error = True
        if not update and not cv:
            # CV obligatoire uniquement à l'ajout
            messages.error(request, "Le CV est obligatoire pour une nouvelle candidature.")
            error = True

        if not error:
            # Affectation des valeurs
            candidature.id_candidat_id = id_candidat
            candidature.lettre_motivation = lettre

            if cv:
                candidature.cv_joint = cv  # mise à jour seulement si fourni

            # Réinitialiser les types
            candidature.id_stage = None
            candidature.id_freelance = None
            candidature.id_formation = None

            if type_cand == "stage":
                candidature.id_stage_id = request.POST.get("id_stage")
            elif type_cand == "freelance":
                candidature.id_freelance_id = request.POST.get("id_freelance")
            elif type_cand == "formation":
                candidature.id_formation_id = request.POST.get("id_formation")

            if update and statut:
                candidature.statut = statut

            candidature.save()
            messages.success(request, f"Candidature {'mise à jour' if update else 'ajoutée'} avec succès !")
            return redirect('liste_candidatures')

    # Pré-remplissage des champs
    type_initial = None
    if post_data:
        type_initial = post_data.get("type")
    else:
        if candidature.id_stage:
            type_initial = "stage"
        elif candidature.id_freelance:
            type_initial = "freelance"
        elif candidature.id_formation:
            type_initial = "formation"

    return render(request, "candidatureapp/form_candidature.html", {
        "update": update,
        "candidature": candidature,
        "utilisateurs": utilisateurs,
        "stages": stages,
        "freelances": freelances,
        "formations": formations,
        "type_initial": type_initial,
        "post_data": post_data,
        "files_data": files_data,
    })

# ------------------------------
# Supprimer une candidature
# ------------------------------
def supprimer_candidature(request, id):
    candidature = get_object_or_404(Candidature, pk=id)

    # Vérification permission
   

    candidature.delete()
    messages.success(request, "Candidature supprimée !")
    return redirect('liste_candidatures')


