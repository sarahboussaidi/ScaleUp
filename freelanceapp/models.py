from django.db import models
from django import forms
from userapp.models import Utilisateur

class Freelance(models.Model):
    DOMAINES = [
        ('IT', 'Informatique / Développement'),
        ('MARKETING', 'Marketing / Communication'),
        ('DESIGN', 'Design / Graphisme'),
        ('FINANCE', 'Finance / Comptabilité'),
        ('RH', 'Ressources Humaines'),
        ('TRAD', 'Traduction / Rédaction'),
        ('EDUCATION', 'Éducation / Formation'),
        ('AUTRE', 'Autre'),
    ]

    id_freelance = models.AutoField(primary_key=True)
    titre_mission = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    competences_requises = models.CharField(max_length=200, blank=True)
    tarif = models.FloatField(blank=True,null=True)
    duree_estimee = models.PositiveIntegerField(blank=True,null=True)  # en jours
    date_publication = models.DateField(auto_now_add=True)
    domaine = models.CharField(max_length=50, choices=DOMAINES, default='IT')
    id_user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, null=True, related_name="freelances")

    def __str__(self):
        return self.titre_mission


class FreelanceForm(forms.ModelForm):
    class Meta:
        model = Freelance
        fields = [
            'titre_mission',
            'description',
            'competences_requises',
            'tarif',
            'duree_estimee',
            'domaine',
        ]
        widgets = {
            'titre_mission': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre de la mission'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Décrivez la mission...'}),
            'competences_requises': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Compétences nécessaires'}),
            'tarif': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tarif en DT', 'step': '0.01'}),
            'duree_estimee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Durée estimée (jours)'}),
            'domaine': forms.Select(attrs={'class': 'form-select'}),
        }

    # ✅ Champs obligatoires gérés via clean_ pour message personnalisé
    def clean_titre_mission(self):
        titre = self.cleaned_data.get('titre_mission')
        if not titre:
            raise forms.ValidationError("Titre de mission manquant.")
        return titre

    def clean_description(self):
        desc = self.cleaned_data.get('description')
        if not desc:
            raise forms.ValidationError("Description manquante.")
        return desc

    def clean_competences_requises(self):
        comp = self.cleaned_data.get('competences_requises')
        if not comp:
            raise forms.ValidationError("Compétences requises manquantes.")
        return comp

    def clean_tarif(self):
        tarif = self.cleaned_data.get('tarif')
        if tarif is None:
            raise forms.ValidationError("Le tarif est obligatoire.")
        if tarif < 0:
            raise forms.ValidationError("Le tarif doit être un nombre positif.")
        if tarif < 20:
            raise forms.ValidationError("Le tarif doit être au moins 20 DT.")
        return tarif

    def clean_duree_estimee(self):
        duree = self.cleaned_data.get('duree_estimee')
        if duree is None:
            raise forms.ValidationError("La durée estimée est obligatoire.")
        if duree <= 0:
            raise forms.ValidationError("La durée doit être supérieure à 0.")
        return duree
