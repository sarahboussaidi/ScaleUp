from django.shortcuts import render, redirect
from .models import Freelance, FreelanceForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator
def list_freelances(request):
   # Récupérer la valeur du filtre GET
    selected_domaine = request.GET.get('domaine', '')

    freelances = Freelance.objects.all()
    if selected_domaine:
        freelances = freelances.filter(domaine=selected_domaine)
 # Filtrage par salaire
    min_value = request.GET.get('min-value')
    max_value = request.GET.get('max-value')

    if min_value:
        freelances = freelances.filter(tarif__gte=min_value)
    if max_value:
        freelances = freelances.filter(tarif__lte=max_value)
    # Trier par tarif croissant
    freelances = freelances.order_by('tarif')
    # Envoyer les domaines au template pour générer les options
    domaines = Freelance.DOMAINES

    context = {
        'freelances': freelances,
        'domaines': domaines,
        'selected_domaine': selected_domaine,
        'min_value': min_value,
        'max_value': max_value,
    }
    paginator = Paginator(freelances, 5)  # 5 offres par page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)  # objet page avec les freelances de cette page

    context = {
        'freelances': page_obj,  # on utilisera page_obj dans le template
    }
   
    return render(request, 'freelanceapp/freelance-list.html', context)

def freelance_grid_2(request):
    # Récupérer la valeur du filtre GET
    selected_domaine = request.GET.get('domaine', '')

    freelances = Freelance.objects.all()
    if selected_domaine:
        freelances = freelances.filter(domaine=selected_domaine)

    # Envoyer les domaines au template pour générer les options
    domaines = Freelance.DOMAINES

    context = {
        'freelances': freelances,
        'domaines': domaines,
        'selected_domaine': selected_domaine,
    }
    
    return render(request, 'freelanceapp/freelance-grid-2.html', context)


@login_required(login_url='login')
def add_freelance(request):
    if request.method == 'POST':
        form = FreelanceForm(request.POST)
        if form.is_valid():
            freelance = form.save(commit=False)
            # ✅ Associer automatiquement l'utilisateur connecté
            freelance.id_user = request.user
            freelance.save()
            # ✅ PAS messages.success ici, mais success=True dans context
            return render(request, 'freelanceapp/freelance-form.html', {
                'form': FreelanceForm(),  # form vide pour le reset
                'success': True,
                'update': False,
            })
        else:
            messages.error(request, "⚠️Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = FreelanceForm()

    return render(request, 'freelanceapp/freelance-form.html', {'form': form})
def update_freelance(request, id):
    freelance = get_object_or_404(Freelance, id_freelance=id)

    # ✅ Vérification que l'utilisateur connecté est le propriétaire
    if freelance.id_user != request.user:
        messages.error(request, "⚠️Vous n'avez pas la permission de modifier cette offre.")
        return redirect('freelance_list')

    if request.method == 'POST':
        form = FreelanceForm(request.POST, instance=freelance)
        if form.is_valid():
            form.save()
            return render(request, 'freelanceapp/freelance-form.html', {
        'form': FreelanceForm(instance=freelance),
        'success': True,
        'update': True,
    })
        else:
            messages.error(request, "⚠️Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = FreelanceForm(instance=freelance)

    return render(request, 'freelanceapp/freelance-form.html', {
        'form': form,
        'freelance': freelance,
        'update': True,  # pour afficher "Modifier la mission" dans le template
    })
def delete_freelance(request, id):
    # Récupérer l'objet ou renvoyer 404
    freelance = get_object_or_404(Freelance, id_freelance=id)

    # Vérification que l'utilisateur connecté est le propriétaire
    if freelance.id_user != request.user:
        messages.error(request, "⚠️Vous n'avez pas la permission de supprimer cette offre.")
        return redirect('freelance_list')

    # Suppression directe
    freelance.delete()

   # Redirection vers la liste avec paramètre deleted=true
    url = f"{reverse('freelance_list')}?deleted=true"
    return redirect(url)


