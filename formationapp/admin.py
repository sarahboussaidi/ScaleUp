from django.contrib import admin
from .models import Formation


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = (
        'titre',
        'categorie',
        'niveau',
        'duree',
        'certif',
        'get_formateur',
    )
    list_filter = ('categorie', 'niveau', 'certif')
    search_fields = ('titre', 'description', 'id_user__username', 'id_user__email')
    ordering = ('categorie', 'titre')
    list_per_page = 15

    fieldsets = (
        ("Informations principales", {
            "fields": (
                'titre',
                'description',
                'categorie',
                'niveau',
                'duree',
                'certif',
            )
        }),
        ("Formateur / Utilisateur lié", {
            "fields": ('id_user',)
        }),
    )

    # Méthode personnalisée pour afficher le nom du formateur
    def get_formateur(self, obj):
        return f"{obj.id_user.username} ({obj.id_user.email})"
    get_formateur.short_description = 'Formateur'
