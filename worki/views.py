from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from stageapp.models import Stage

@login_required
def index(request):
    stages = Stage.objects.all()
    return render(request, 'index.html', {'stages': stages})
