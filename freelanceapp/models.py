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
    id_freelance=models.AutoField(primary_key=True)
    titre_mission=models.CharField(max_length=100)
    description=models.TextField()
    competences_requises=models.CharField(max_length=200)
    tarif=models.FloatField()
    duree_estimee=models.IntegerField()
    date_publication=models.DateField(auto_now_add=True)
    domaine = models.CharField( max_length=50,choices=DOMAINES,default='IT')
    id_user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE,null=True, related_name="freelances")

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
            'tarif': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Tarif en DT'}),
            'duree_estimee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Durée estimée (jours)'}),
            'domaine': forms.Select(attrs={'class': 'form-select'}),
        }