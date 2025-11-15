from django.contrib import admin # type: ignore
from django.contrib.auth.admin import UserAdmin # type: ignore
from .models import Utilisateur, Candidat, Entreprise, Admin, Domain, Skill , Language

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
class LanguageInline(admin.TabularInline):
    model = Language
    extra = 1

# ---------------------------
# Role-specific Inlines
# ---------------------------
class CandidatInline(admin.StackedInline):
    model = Candidat
    filter_horizontal = ['skills']

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
        if not obj:
            return []

        inlines = []

        if obj.role == 'candidat':
            inlines = [
                CandidatInline(self.model, self.admin_site),
                LanguageInline(self.model, self.admin_site)  # 👈 ADD LANGUAGES HERE
            ]
        elif obj.role == 'entreprise':
            inlines = [EntrepriseInline(self.model, self.admin_site)]
        elif obj.role == 'admin':
            inlines = [AdminInline(self.model, self.admin_site)]

        return inlines

    def save_model(self, request, obj, form, change):
        if not change and not obj.role:
            obj.role = 'candidat'
        super().save_model(request, obj, form, change)