from django.contrib import admin
from .models import Freelance


@admin.register(Freelance)
class FreelanceAdmin(admin.ModelAdmin):
    list_display = (
        'titre_mission',
        'domaine',
        'tarif',
        'duree_estimee',
        'date_publication',
        'get_entreprise',
    )
    list_filter = ('domaine', 'date_publication')
    search_fields = ('titre_mission', 'description', 'competences_requises', 'id_entreprise__nom_entreprise')
    ordering = ('-date_publication',)
    list_per_page = 15

    fieldsets = (
        ("Détails de la mission", {
            "fields": (
                'titre_mission',
                'description',
                'competences_requises',
                'domaine',
                'tarif',
                'duree_estimee',
            )
        }),
        ("Informations entreprise", {
            "fields": ('id_entreprise',)
        }),
        ("Publication", {
            "fields": ('date_publication',)
        }),
    )

    readonly_fields = ('date_publication',)

    # Méthode personnalisée pour afficher le nom de l'entreprise
    def get_entreprise(self, obj):
        return obj.id_entreprise.nom_entreprise if obj.id_entreprise else "—"
    get_entreprise.short_description = 'Entreprise'
