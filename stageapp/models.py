from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from datetime import date
from userapp.models import Entreprise  


titleValidator = RegexValidator(
    r'^[a-zA-ZÀ-ÿ\s]+$',
    'Le titre ne doit contenir que des lettres et des espaces.'
)

localisationValidator = RegexValidator(
    r'^[a-zA-ZÀ-ÿ\s,]+$',
    'La localisation ne doit contenir que des lettres, espaces et virgules.'
)

typeValidator = RegexValidator(
    r'^[a-zA-Z\s]+$',
    'Le type doit contenir uniquement des lettres et espaces.'
)

class Stage(models.Model):
    id_stage = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=100, validators=[titleValidator])
    description = models.TextField()
    localisation = models.CharField(max_length=100, validators=[localisationValidator])
    duree = models.PositiveIntegerField(help_text="Durée du stage en semaines")
    date_publication = models.DateField(default=date.today)
    type = models.CharField(max_length=50, validators=[typeValidator])
    
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name='stages'
    )
    def clean(self):
        if self.duree <= 0:
            raise ValidationError("La durée du stage doit être supérieure à 0.")
        if self.date_publication > date.today():
            raise ValidationError("La date de publication ne peut pas être dans le futur.")
        super().clean()

    # ────────────── DISPLAY ──────────────
    def __str__(self):
        return f"{self.titre} ({self.entreprise.nom_entreprise})"