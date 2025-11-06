from django.shortcuts import render

# Create your views here.

def signin_view(request):
    # This will render the shared template page-about.html
    return render(request, 'page-signin.html')

def register_view(request):
    # This will render the shared template page-register.html
    return render(request, 'page-register.html')