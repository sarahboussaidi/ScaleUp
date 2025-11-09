from django.shortcuts import render, redirect
from .models import Freelance, FreelanceForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404

def list_freelances(request):
    freelances = Freelance.objects.all()
    return render(request, 'freelance-list.html', {'freelances': freelances})


def freelance_grid_2(request):
    freelances = Freelance.objects.all()
    return render(request, 'freelance-grid-2.html', {'freelances': freelances})


@login_required(login_url='login')
def add_freelance(request):
    if request.method == 'POST':
        form = FreelanceForm(request.POST)
        if form.is_valid():
            freelance = form.save(commit=False)
            # ✅ Associer automatiquement l'utilisateur connecté
            freelance.id_user = request.user
            freelance.save()
            messages.success(request, "Mission ajoutée avec succès !")
            return redirect('list')
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = FreelanceForm()

    return render(request, 'freelance-form.html', {'form': form})
def update_freelance(request, id):
    freelance = get_object_or_404(Freelance, id_freelance=id)

    # ✅ Vérification que l'utilisateur connecté est le propriétaire
    if freelance.id_user != request.user:
        messages.error(request, "Vous n'avez pas la permission de modifier cette offre.")
        return redirect('list')

    if request.method == 'POST':
        form = FreelanceForm(request.POST, instance=freelance)
        if form.is_valid():
            form.save()
            messages.success(request, "Mission mise à jour avec succès !")
            return redirect('list')
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = FreelanceForm(instance=freelance)

    return render(request, 'freelance-form.html', {
        'form': form,
        'freelance': freelance,
        'update': True,  # pour afficher "Modifier la mission" dans le template
    })
def delete_freelance(request, id):
    freelance = get_object_or_404(Freelance, id_freelance=id)

    # Vérification que l'utilisateur connecté est le propriétaire
    if freelance.id_user != request.user:
        messages.error(request, "Vous n'avez pas la permission de supprimer cette offre.")
        return redirect('list')

    if request.method == 'POST':
        freelance.delete()
        messages.success(request, "Mission supprimée avec succès !")
        return redirect('list')

    # Optionnel : demander confirmation avant suppression
    return render(request, 'freelance-confirm-delete.html', {'freelance': freelance})
def login_view(request):
    return render(request, 'index.html')


def register_view(request):
    return render(request, 'index.html')


def home_view(request):
    return render(request, 'index.html')
def logout_view(request):
    return redirect('admin:login')