from django.db import models
from userapp.models import Utilisateur
from freelanceapp.models import Freelance
from stageapp.models import Stage
from formationapp.models import Formation

class Candidature(models.Model):
    STATUTS = [
        ('EN_ATTENTE', 'En attente'),
        ('VUE', 'Vue par entreprise'),
        ('ENTRETIEN', 'Entretien prévu'),
        ('ACCEPTEE', 'Acceptée'),
        ('REFUSEE', 'Refusée'),
    ]

    id_candidature = models.AutoField(primary_key=True)
    id_candidat = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="candidatures")
    id_stage = models.ForeignKey(Stage, on_delete=models.CASCADE, null=True, blank=True, related_name="candidatures_stage")
    id_freelance = models.ForeignKey(Freelance, on_delete=models.CASCADE, null=True, blank=True, related_name="candidatures_freelance")
    id_formation = models.ForeignKey(Formation, on_delete=models.CASCADE, null=True, blank=True, related_name="candidatures_formation")

    cv_joint = models.FileField(upload_to='cvs/', null=True, blank=True)
    lettre_motivation = models.TextField(null=True, blank=True)
    date_candidature = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='EN_ATTENTE')

   

    class Meta:
        verbose_name = "Candidature"
        verbose_name_plural = "Candidatures"
        ordering = ['-date_candidature']