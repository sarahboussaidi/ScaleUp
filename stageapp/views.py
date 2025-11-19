from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Stage
from .forms import StageForm
from userapp.models import Entreprise
from django.db.models import Q




@login_required
def stage_list(request):
    stages = Stage.objects.all().select_related('entreprise')

    search = request.GET.get('search')
    tri = request.GET.get('tri')

    if search:
        stages = stages.filter(
            Q(titre__icontains=search) |
            Q(entreprise__nom_entreprise__icontains=search) |
            Q(localisation__icontains=search)
        )
    if tri == "recent":
        stages = stages.order_by('-id_stage')
    elif tri == "ancien":
        stages = stages.order_by('id_stage')
    elif tri == "duree":
        stages = stages.order_by('-duree')
    
    duree_min = request.GET.get('duree_min')
    duree_max = request.GET.get('duree_max')
    if duree_min:
        stages = stages.filter(duree__gte=int(duree_min))
    if duree_max:
        stages = stages.filter(duree__lte=int(duree_max))


    # Priorité entreprise
    if request.user.is_authenticated and request.user.role == 'entreprise':
        stages = sorted(stages, key=lambda s: s.entreprise.id != request.user.id)

    return render(request, 'stageapp/stage_list.html', {'stages': stages})


@login_required
def stage_detail(request, id_stage):
    stage = get_object_or_404(Stage, id_stage=id_stage)
    return render(request, 'stageapp/stage_detail.html', {'stage': stage})

@login_required
def stage_create(request):
    if request.user.role != 'entreprise':
        return HttpResponseForbidden("Seules les entreprises peuvent créer des stages")
    
    # Récupérer l'instance Entreprise de l'utilisateur connecté
    try:
        entreprise_instance = Entreprise.objects.get(id=request.user.id)
    except Entreprise.DoesNotExist:
        return HttpResponseForbidden("Profil entreprise non trouvé")
    
    if request.method == 'POST':
        form = StageForm(request.POST)
        if form.is_valid():
            stage = form.save(commit=False)
            stage.entreprise = entreprise_instance  # Associer l'entreprise réelle
            stage.save()
            return redirect('stage_list')
    else:
        form = StageForm()
    
    return render(request, 'stageapp/stage_form.html', {'form': form})

@login_required
def stage_update(request, id_stage):
    stage = get_object_or_404(Stage, id_stage=id_stage)
    
    # Vérifier si l'utilisateur est l'entreprise propriétaire
    if request.user.role != 'entreprise' or stage.entreprise.id != request.user.id:
        return HttpResponseForbidden("Vous ne pouvez modifier que vos propres stages")
    
    if request.method == 'POST':
        form = StageForm(request.POST, instance=stage)
        if form.is_valid():
            form.save()
            return redirect('stage_list')
    else:
        form = StageForm(instance=stage)
    
    return render(request, 'stageapp/stage_form.html', {'form': form})

@login_required
def stage_delete(request, id_stage):
    stage = get_object_or_404(Stage, id_stage=id_stage)
    
    # Vérifier si l'utilisateur est l'entreprise propriétaire
    if request.user.role != 'entreprise' or stage.entreprise.id != request.user.id:
        return HttpResponseForbidden("Vous ne pouvez supprimer que vos propres stages")
    
    if request.method == 'POST':
        stage.delete()
        return redirect('stage_list')
    
    return render(request, 'stageapp/stage_confirm_delete.html', {'stage': stage})