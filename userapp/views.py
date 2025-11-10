from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()

def register_view(request):
    if request.method == "POST":
        fullname = request.POST.get('fullname')
        email = request.POST.get('emailaddress')
        username = request.POST.get('username')
        password = request.POST.get('password')
        repassword = request.POST.get('re-password')
        role = request.POST.get('role')  # 👈 added

        if password != repassword:
            messages.error(request, "Passwords do not match.")
            return render(request, "page-register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "page-register.html")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return render(request, "page-register.html")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=fullname,
            role=role  # 👈 assign selected role
        )
        user.save()
        messages.success(request, "Account created successfully! Please sign in.")
        return redirect('signin')

    return render(request, "page-register.html")

def signin_view(request):
    if request.method == "POST":
        username = request.POST.get('fullname')  # matches your HTML name
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')  # change 'home' to your main page name
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "page-signin.html")