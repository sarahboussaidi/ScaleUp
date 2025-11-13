from django.db import models
from userapp.models import Utilisateur
from django.core.validators import MinLengthValidator


class Formation(models.Model):
    NIVEAUX = [
        ('DEBUTANT', 'Debutant'),
        ('INTERMEDIAIRE', 'Intermediaire'),
        ('AVANCE', 'Avancé'),
    ]

    CATEGORIES = [
        ('IT', 'Informatique / Développement'),
        ('MARKETING', 'Marketing / Communication'),
        ('DESIGN', 'Design / Graphisme'),
        ('FINANCE', 'Finance / Comptabilité'),
        ('RH', 'Ressources Humaines'),
        ('TRAD', 'Traduction / Rédaction'),
        ('EDUCATION', 'Éducation / Formation'),
        ('AUTRE', 'Autre'),
    ]

    id_formation = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=100)
    description = models.TextField(validators=[MinLengthValidator(10)])
    niveau = models.CharField(max_length=30, choices=NIVEAUX, default='DEBUTANT')
    categorie = models.CharField(max_length=50, choices=CATEGORIES, default='IT')
    duree = models.PositiveBigIntegerField()
    certif = models.BooleanField(default=False)
    image = models.ImageField(upload_to='formation/', blank=True, null=True)
    id_user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="formations")
    

    def __str__(self):
        return self.titre

