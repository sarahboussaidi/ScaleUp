from django.contrib import admin
from .models import Candidature


@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = (
        'id_candidature',
        'get_candidat',
        'get_type_offre',
        'date_candidature',
        'statut',
    )
    list_filter = ('statut', 'date_candidature')
    search_fields = (
        'id_candidat__username',
        'id_candidat__email',
        'id_stage__titre',
        'id_freelance__titre_mission',
        'id_formation__titre',
    )
    ordering = ('-date_candidature',)
    readonly_fields = ('date_candidature',)
    list_per_page = 20

    fieldsets = (
        ("Informations générales", {
            'fields': (
                'id_candidat',
                'id_stage',
                'id_freelance',
                'id_formation',
                'cv_joint',
                'lettre_motivation',
            )
        }),
        ("Suivi de la candidature", {
            'fields': ('statut', 'date_candidature')
        }),
    )

    # ============================
    # Méthodes d'affichage personnalisées
    # ============================
    def get_candidat(self, obj):
        return f"{obj.id_candidat.username} ({obj.id_candidat.email})"
    get_candidat.short_description = 'Candidat'

    def get_type_offre(self, obj):
        if obj.id_stage:
            return f"Stage : {obj.id_stage.titre}"
        elif obj.id_freelance:
            return f"Freelance : {obj.id_freelance.titre_mission}"
        elif obj.id_formation:
            return f"Formation : {obj.id_formation.titre}"
        return "Aucune"
    get_type_offre.short_description = 'Offre liée'
