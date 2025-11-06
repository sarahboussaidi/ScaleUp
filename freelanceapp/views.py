from django.shortcuts import render
from .models import Freelance

def list_freelances(request):
    freelances = Freelance.objects.all()
    return render(request, 'freelance-list.html', {'freelances': freelances})
def freelance_grid_2(request):
    freelances = Freelance.objects.all().order_by('-date_publication')
    return render(request, 'freelance-grid-2.html', {'freelances': freelances})