from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .models import Candidature, Utilisateur, Stage, Freelance, Formation

# ------------------------------
# Liste des candidatures
# ------------------------------
@login_required(login_url='login')
def liste_candidatures(request):
    candidatures = Candidature.objects.all().order_by('-date_candidature')
    return render(request, 'liste_candidature.html', {'candidatures': candidatures})


# ------------------------------
# Ajouter ou modifier une candidature
# ------------------------------
@login_required(login_url='login')

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

    # Pour pré-remplissage avec POST en cas d'erreur
    post_data = request.POST if request.method == "POST" else None

    if request.method == "POST":
        # Récupération des valeurs du formulaire
        id_candidat = request.POST.get("id_candidat")
        type_cand = request.POST.get("type")
        lettre = request.POST.get("lettre_motivation")
        cv = request.FILES.get("cv_joint")
        statut = request.POST.get("statut") if update else None

        # Validation simple
        if not id_candidat:
            messages.error(request, "Veuillez choisir un candidat.")
        elif not type_cand:
            messages.error(request, "Veuillez choisir le type.")
        elif not lettre or lettre.strip() == "":
            messages.error(request, "Veuillez rédiger une lettre de motivation.")
        else:
            # Affectation des valeurs
            candidature.id_candidat_id = id_candidat
            candidature.lettre_motivation = lettre

            if cv:
                candidature.cv_joint = cv  # Mise à jour seulement si un nouveau fichier est fourni

            # Réinitialisation des types pour éviter conflits
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

    # Pré-remplissage des champs pour le formulaire
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

    return render(request, "form_candidature.html", {
        "update": update,
        "candidature": candidature,
        "utilisateurs": utilisateurs,
        "stages": stages,
        "freelances": freelances,
        "formations": formations,
        "type_initial": type_initial,
        "post_data": post_data,  # <-- envoyé au template
    })



# ------------------------------
# Supprimer une candidature
# ------------------------------
@login_required(login_url='login')
def supprimer_candidature(request, id):
    candidature = get_object_or_404(Candidature, pk=id)

    # Vérification si l'utilisateur peut supprimer
    if not request.user.is_superuser:  # ou autre logique selon ton projet
        messages.error(request, "⚠️ Vous n'avez pas la permission de supprimer cette candidature.")
        return redirect('liste_candidatures')

    candidature.delete()
    messages.success(request, "Candidature supprimée !")
    return redirect('liste_candidatures')
# ------------------------------
# Authentification
# ------------------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('liste_candidatures')
        else:
            messages.error(request, "Identifiants incorrects")

    return render(request, 'login.html')


@login_required(login_url='login')
def logout_view(request):
    logout(request)
    return redirect('login')


def register_view(request):
    return render(request, 'register.html')
