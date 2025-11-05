from django.contrib import admin
from .models import Stage


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = (
        'titre',
        'entreprise',
        'localisation',
        'type',
        'duree',
        'date_publication',
    )
    list_filter = ('type', 'date_publication', 'entreprise__nom_entreprise')
    search_fields = (
        'titre',
        'description',
        'localisation',
        'entreprise__nom_entreprise',
        'entreprise__email',
    )
    ordering = ('-date_publication',)
    list_per_page = 15
    readonly_fields = ('date_publication',)

    fieldsets = (
        ("Informations sur le stage", {
            "fields": (
                'titre',
                'description',
                'localisation',
                'type',
                'duree',
            )
        }),
        ("Entreprise associée", {
            "fields": ('entreprise',)
        }),
        ("Date de publication", {
            "fields": ('date_publication',)
        }),
    )

    # ────────────── MÉTHODES PERSONNALISÉES ──────────────
    def get_queryset(self, request):
        """Optimisation des requêtes pour éviter les multiples accès à la base"""
        return super().get_queryset(request).select_related('entreprise')

    def entreprise_nom(self, obj):
        """Affiche le nom de l’entreprise plutôt que son ID"""
        return obj.entreprise.nom_entreprise
    entreprise_nom.short_description = 'Entreprise'
