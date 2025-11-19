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
        'get_utilisateur',
    )
    list_filter = ('domaine', 'date_publication')
    search_fields = ('titre_mission', 'description', 'competences_requises', 'id_user__username')
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
        ("Informations utilisateur", {
            "fields": ('id_user',)
        }),
        ("Publication", {
            "fields": ('date_publication',)
        }),
    )

    readonly_fields = ('date_publication',)

    # Méthode personnalisée pour afficher le nom de l'utilisateur
    def tarif(self, obj):
        return f"{obj.tarif:.2f} DT"  # affiche 2 décimales + unité
    tarif.short_description = "Tarif"

    def duree_estimee(self, obj):
        return f"{obj.duree_estimee} jours"
    duree_estimee.short_description = "Durée estimée"

    def get_utilisateur(self, obj):
        return obj.id_user.username if obj.id_user else "—"
    get_utilisateur.short_description = 'Utilisateur'
