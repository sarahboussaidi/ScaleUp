from django.shortcuts import render
from .models import Freelance, FreelanceForm
from django import forms
from django.shortcuts import redirect

def list_freelances(request):
    freelances = Freelance.objects.all()
    return render(request, 'freelance-list.html', {'freelances': freelances})
def freelance_grid_2(request):
    freelances = Freelance.objects.all()
    return render(request, 'freelance-grid-2.html', {'freelances': freelances})

def add_freelance(request):
    if request.method == 'POST':
        form = FreelanceForm(request.POST)
        if form.is_valid():
            freelance = form.save(commit=False)
            freelance.id_user = request.user  # si tu utilises le modèle Utilisateur
            freelance.save()
            return redirect('list')
    else:
        form = FreelanceForm()
    return render(request, 'freelance-form.html', {'form': form})