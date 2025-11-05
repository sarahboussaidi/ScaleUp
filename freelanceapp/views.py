from django.shortcuts import render

# Create your views here.
def list_freelances(request):
    return render(request, 'job-grid.html')
