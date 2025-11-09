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
    titre_mission = models.CharField(max_length=100)
    description = models.TextField()
    competences_requises = models.CharField(max_length=200)
    tarif = models.FloatField()
    duree_estimee = models.PositiveIntegerField()
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
            'titre_mission': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre de la mission',
                'required': 'required'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez la mission...',
                'required': 'required'
            }),
            'competences_requises': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Compétences nécessaires',
                'required': 'required'
            }),
            'tarif': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tarif en DT',
                'required': 'required',
                'step': '0.01',
                'min': '0'
            }),
            'duree_estimee': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Durée estimée (jours)',
                'required': 'required',
                'min': '1'
            }),
            'domaine': forms.Select(attrs={
                'class': 'form-select',
                'required': 'required'
            }),
        }

    def clean_tarif(self):
        tarif = self.cleaned_data.get('tarif')
        if tarif is not None and tarif < 0:
            raise forms.ValidationError("Le tarif doit être un nombre positif.")
        return tarif

    def clean_duree_estimee(self):
        duree = self.cleaned_data.get('duree_estimee')
        if duree is not None and duree <= 0:
            raise forms.ValidationError("La durée doit être supérieure à 0.")
        return duree
