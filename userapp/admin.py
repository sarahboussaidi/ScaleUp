from django.contrib import admin # type: ignore
from django.contrib.auth.admin import UserAdmin # type: ignore
from .models import Utilisateur, Candidat, Entreprise, Admin, Domain, Skill, Language

# ---------------------------
# Domain & Skill Admins
# ---------------------------
@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["name"]

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["name", "domain"]
    list_filter = ["domain"]

# ---------------------------
# Language Inline for Candidat
# ---------------------------
class LanguageInline(admin.TabularInline):
    model = Language
    extra = 1
    fields = ("name", "proficiency")

# ---------------------------
# Role-specific Inlines
# ---------------------------
class CandidatInline(admin.StackedInline):
    model = Candidat
    filter_horizontal = ['skills']
    inlines = [LanguageInline]

class EntrepriseInline(admin.StackedInline):
    model = Entreprise

class AdminInline(admin.StackedInline):
    model = Admin

# ---------------------------
# Main Utilisateur Admin
# ---------------------------
@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('email', 'username', 'role', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('role', 'is_active', 'is_staff')

    fieldsets = (
        ('Login Info', {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'first_name', 'last_name', 'telephone', 'adresse', 'photo')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_active', 'is_staff', 'role')
        }),
    )

    def get_inline_instances(self, request, obj=None):
        """
        Return only the inline corresponding to the user's role
        """
        if not obj:
            return []

        if obj.role == 'candidat':
            return [CandidatInline(self.model, self.admin_site)]
        elif obj.role == 'entreprise':
            return [EntrepriseInline(self.model, self.admin_site)]
        elif obj.role == 'admin':
            return [AdminInline(self.model, self.admin_site)]
        return []

    def save_model(self, request, obj, form, change):
        """
        Ensure role is set when creating a new user
        """
        if not change and not obj.role:
            obj.role = 'candidat'
        super().save_model(request, obj, form, change)
