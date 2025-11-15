from django.shortcuts import render, redirect # type: ignore
from django.contrib.auth import authenticate, login, logout, get_user_model # type: ignore
from django.contrib import messages # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from .models import Candidat, Entreprise, Admin

User = get_user_model()


# ---------------------------
# Logout
# ---------------------------
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('signin')


# ---------------------------
# Profile View
# ---------------------------
@login_required
def profile_view(request):
    user = request.user

    if user.role == 'candidat':
        candidat = getattr(user, 'candidat', None)
        if not candidat:
            messages.error(request, "No Candidat profile found.")
            return redirect('home')
        return render(request, 'candidates-single.html', {
            'user': user,
            'candidat': candidat
        })

    elif user.role == 'entreprise':
        entreprise = getattr(user, 'entreprise', None)
        if not entreprise:
            messages.error(request, "No Entreprise profile found.")
            return redirect('home')
        return render(request, 'employers-single.html', {
            'user': user,
            'entreprise': entreprise
        })

    elif user.role == 'admin':
        return redirect('/admin/')

    return redirect('home')


# ---------------------------
# Update Profile
# ---------------------------
@login_required
def update_profile(request):
    user = request.user

    if request.method == 'POST':
        # General user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.adresse = request.POST.get('adresse', getattr(user, 'adresse', ''))
        user.telephone = request.POST.get('telephone', getattr(user, 'telephone', ''))
        user.bio = request.POST.get('bio', getattr(user, 'bio', ''))
        user.save()

        # Role-specific updates
        if user.role == 'candidat':
            candidat = getattr(user, 'candidat', None)
            if candidat:
                candidat.years_experience = request.POST.get('years_experience', candidat.years_experience)
                candidat.education_level = request.POST.get('education_level', candidat.education_level)
                candidat.save()

        elif user.role == 'entreprise':
            entreprise = getattr(user, 'entreprise', None)
            if entreprise:
                entreprise.nom_entreprise = request.POST.get('nom_entreprise', entreprise.nom_entreprise)
                entreprise.domaine = request.POST.get('domaine', entreprise.domaine)
                entreprise.site_web = request.POST.get('site_web', entreprise.site_web)
                entreprise.save()

        messages.success(request, "Profile updated successfully.")
        return redirect('profile')

    return render(request, 'profile_edit.html', {'user': user})


# ---------------------------
# Delete Account
# ---------------------------
@login_required
def delete_account(request):
    user = request.user
    user.delete()
    messages.success(request, "Your account has been deleted.")
    return redirect('home')


# ---------------------------
# Register
# ---------------------------
def register_view(request):
    if request.method == "POST":
        fullname = request.POST.get('fullname', '')
        email = request.POST.get('emailaddress', '')
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        repassword = request.POST.get('re-password', '')
        role = request.POST.get('role', '')

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
            role=role
        )

        # Create role-specific object
        if role == 'candidat':
            Candidat.objects.get_or_create(user=user)
        elif role == 'entreprise':
            Entreprise.objects.get_or_create(user=user)
        elif role == 'admin':
            Admin.objects.get_or_create(user=user)

        messages.success(request, "Account created successfully! Please sign in.")
        return redirect('signin')

    return render(request, "page-register.html")


# ---------------------------
# Sign-in
# ---------------------------
def signin_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            return redirect('profile')
        else:
            messages.error(request, "Invalid email or password")
    return render(request, "page-signin.html")
