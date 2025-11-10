from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Admin, Entreprise, Candidat , Domain, Skill


# ===============================
# CONFIGURATION DE BASE : UTILISATEUR
# ===============================
@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    exclude = ('groups', 'user_permissions', 'last_login', 'date_joined')
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('date_joined',)
    fieldsets = (
        ("Informations de connexion", {
            "fields": ("username", "email", "password")
        }),
        ("Informations personnelles", {
            "fields": ("first_name", "last_name", "telephone", "adresse", "photo")
        }),
        ("Rôle et permissions", {
            "fields": ("role", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        ("Dates importantes", {
            "fields": ("last_login", "date_joined")
        }),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role", "is_active", "is_staff"),
        }),
    )


# ===============================
# ADMIN : ENTREPRISE
# ===============================
@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    exclude = ('groups', 'user_permissions', 'last_login', 'date_joined')
    list_display = ('nom_entreprise', 'email', 'domaine', 'site_web', 'is_active')
    search_fields = ('nom_entreprise', 'email', 'domaine')
    list_filter = ('domaine', 'is_active')
    ordering = ('nom_entreprise',)


# ===============================
# ADMIN : CANDIDAT
# ===============================
@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'domain']
    list_filter = ['domain']

@admin.register(Candidat)
class CandidatAdmin(admin.ModelAdmin):
    exclude = ('groups', 'user_permissions', 'last_login', 'date_joined')
    list_display = ('username', 'email', 'age', 'telephone', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_active',)
    ordering = ('username',)
    filter_horizontal = ['skills'] 


# ===============================
# ADMIN : ADMIN (RÔLE)
# ===============================
@admin.register(Admin)
class AdminAppAdmin(admin.ModelAdmin):
    exclude = ('groups', 'user_permissions', 'last_login', 'date_joined')
    list_display = ('username', 'email', 'niveau_acces', 'is_staff', 'is_superuser')
    list_filter = ('niveau_acces', 'is_superuser', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('username',)
