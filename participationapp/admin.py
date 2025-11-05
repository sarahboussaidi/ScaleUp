from django.contrib import admin
from .models import Participation


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = (
        'id_particip',
        'get_utilisateur',
        'get_formation',
        'date_particip',
    )
    list_filter = ('date_particip', 'id_formation__categorie')
    search_fields = (
        'id_user__username',
        'id_user__email',
        'id_formation__titre',
        'id_formation__categorie',
    )
    ordering = ('-date_particip',)
    readonly_fields = ('date_particip',)
    list_per_page = 20

    fieldsets = (
        ("Informations de participation", {
            "fields": (
                'id_user',
                'id_formation',
                'date_particip',
            )
        }),
    )

    # Méthode pour afficher le nom complet de l'utilisateur
    def get_utilisateur(self, obj):
        return f"{obj.id_user.username} ({obj.id_user.email})"
    get_utilisateur.short_description = 'Participant'

    # Méthode pour afficher le titre de la formation
    def get_formation(self, obj):
        return obj.id_formation.titre
    get_formation.short_description = 'Formation'
