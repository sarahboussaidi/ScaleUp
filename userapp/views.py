from django.shortcuts import render, redirect # type: ignore
from django.contrib.auth import authenticate, login, logout, get_user_model # type: ignore
from django.contrib import messages # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from .models import Candidat, Entreprise, Admin , Domain, Skill, Utilisateur

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
    candidat = getattr(user, "candidat", None)
    entreprise = getattr(user, "entreprise", None)
    admin_profile = getattr(user, "admin", None)

    context = {
        "user": user,
        "candidat": candidat,
        "entreprise": entreprise,
        "admin_profile": admin_profile,
        "domains": Domain.objects.all(),
        "skills": Skill.objects.all(),

    }

    if candidat:
        return render(request, "candidates-single.html", context)
    elif entreprise:
        return render(request, "employers-single.html", context)
    else:
        return redirect("/admin/")

# ---------------------------
# Update Profile
# ---------------------------
@login_required
def update_profile(request):
    user = request.user

    # Get linked roles safely
    candidat = getattr(user, "candidat", None)
    entreprise = getattr(user, "entreprise", None)

    if request.method == "POST":

        # ------------- UPDATE USER FIELDS -------------
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.adresse = request.POST.get("adresse", user.adresse)
        user.telephone = request.POST.get("telephone", user.telephone)

        # Photo
        if request.FILES.get("photo"):
            user.photo = request.FILES["photo"]

        user.save()

        # ----------------- Handle Languages -----------------
        if candidat:
            # ----- Update Candidat fields -----
            candidat.age = request.POST.get("age", candidat.age)
            candidat.cv = request.FILES.get("cv") or candidat.cv
            candidat.portfolio_website = request.POST.get("portfolio_website", candidat.portfolio_website)
            candidat.years_experience = request.POST.get("years_experience", candidat.years_experience)
            candidat.education_level = request.POST.get("education_level", candidat.education_level)
            candidat.bio = request.POST.get("bio", candidat.bio)
            candidat.save()

        # ------------- UPDATE ENTREPRISE FIELDS -------------
        if entreprise:
            entreprise.nom_entreprise = request.POST.get("nom_entreprise", entreprise.nom_entreprise)
            entreprise.domaine = request.POST.get("domaine", entreprise.domaine)
            entreprise.site_web = request.POST.get("site_web", entreprise.site_web)
            entreprise.description = request.POST.get("description", entreprise.description)
            entreprise.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    # GET → show the form page
    from .models import Domain
    domains = Domain.objects.all()

    context = {
        "user": user,
        "candidat": candidat,
        "entreprise": entreprise,
        "domains": domains,
    }

    return render(request, "profile_edit.html", context)


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
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        firstname = request.POST.get('firstname', '')
        lastname = request.POST.get('lastname', '')
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
            first_name=firstname,
            last_name=lastname,
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
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password")
            return redirect('signin')

    return render(request, "page-signin.html")
