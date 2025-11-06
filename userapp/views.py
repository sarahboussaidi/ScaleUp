from django.shortcuts import render

# Create your views here.

def about_view(request):
    # This will render the shared template page-about.html
    return render(request, 'page-about.html')
