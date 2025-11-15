from django.shortcuts import render, redirect # type: ignore
from django.contrib.auth import authenticate, login, logout, get_user_model # type: ignore
from django.contrib import messages     # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore
from .models import Candidat, Entreprise, Admin, Domain, Skill # type: ignore
from django.db import models # type: ignore

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
    candidat = getattr(user, "candidat", None)
    entreprise = getattr(user, "entreprise", None)

    if request.method == "POST":
        # ----------------- Update Utilisateur fields -----------------
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.email = request.POST.get("email", user.email)
        user.adresse = request.POST.get("adresse", user.adresse)
        user.telephone = request.POST.get("telephone", user.telephone)

        if request.FILES.get("photo"):
            user.photo = request.FILES["photo"]

        user.save()

        # ----------------- Update Candidat fields -----------------
        if candidat:
            candidat.age = request.POST.get("age", candidat.age)
            candidat.portfolio_website = request.POST.get("portfolio_website", candidat.portfolio_website)
            candidat.years_experience = request.POST.get("years_experience", candidat.years_experience)
            candidat.education_level = request.POST.get("education_level", candidat.education_level)
            candidat.bio = request.POST.get("bio", candidat.bio)

            if request.FILES.get("cv"):
                candidat.cv = request.FILES["cv"]

            skill_ids = request.POST.getlist("skills")
            if skill_ids:
                candidat.skills.set(Skill.objects.filter(id__in=skill_ids))
            else:
                candidat.skills.clear()

            candidat.save()

        # ----------------- Update Entreprise fields -----------------
        if entreprise:
            entreprise.nom_entreprise = request.POST.get("nom_entreprise", entreprise.nom_entreprise)
            entreprise.domaine = request.POST.get("domaine", entreprise.domaine)
            entreprise.adresse = request.POST.get("adresse", entreprise.adresse)
            entreprise.telephone = request.POST.get("telephone", entreprise.telephone)
            entreprise.site_web = request.POST.get("site_web", entreprise.site_web)
            entreprise.description = request.POST.get("description", entreprise.description)
            entreprise.save()
            if request.FILES.get("photo"):
                user.photo = request.FILES["photo"]

            entreprise.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    # ----------------- GET → show form -----------------
    context = {
        "user": user,
        "candidat": candidat,
        "entreprise": entreprise,
        "domains": Domain.objects.all(),
    }
    
    return render(request, "employers-single.html" if entreprise else "candidat-single.html", context)


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



@login_required
def candidats_listing(request):

    candidates = Candidat.objects.all()

    # ------------------- GET FILTERS -------------------
    search_query = request.GET.get("search", "").strip()
    domain_filter = request.GET.get("domain", "")
    skill_filter = request.GET.get("skill", "")
    education_filter = request.GET.get("education", "")
    min_experience = request.GET.get("experience", "")

    # ------------------- APPLY FILTERS -------------------

    # Search by skill text OR user first_name/last_name
    if search_query:
        candidates = candidates.filter(
            models.Q(user__first_name__icontains=search_query) |
            models.Q(user__last_name__icontains=search_query) |
            models.Q(skills__name__icontains=search_query)
        ).distinct()

    # Filter by domain (Skill → Domain)
    if domain_filter:
        candidates = candidates.filter(
            skills__domain__id=domain_filter
        ).distinct()

    # Filter by specific skill ID
    if skill_filter:
        candidates = candidates.filter(
            skills__id=skill_filter
        ).distinct()

    # Filter by education level
    if education_filter:
        candidates = candidates.filter(
            education_level=education_filter
        )

    # Filter by minimum years of experience
    if min_experience.isdigit():
        candidates = candidates.filter(
            years_experience__gte=int(min_experience)
        )
    selected_domain = None
    domain_id = request.GET.get('domain')

    if domain_id:
        try:
            selected_domain = Domain.objects.get(id=domain_id)

        except:
            selected_domain = None

    selected_skill = None
    skill_id = request.GET.get("skill")

    if skill_id:
        try:
            selected_skill = Skill.objects.get(id=skill_id)
        except Skill.DoesNotExist:
            selected_skill = None
    context = {
        "candidates": candidates.distinct(),
        "domains": Domain.objects.all(),
        "skills": Skill.objects.all(),
        "selected_domain": selected_domain,
        "selected_skill": selected_skill,
    }

    
    return render(request, 'candidates-grid.html', context)

@login_required
def candidat_detail(request, candidat_id):
    candidate = Candidat.objects.filter(id=candidat_id).first()
    if not candidate:
        messages.error(request, "Candidate not found")
        return redirect('candidats_listing')

    context = {'candidate': candidate}
    return render(request, 'candidates-single.html', context)
