from django.db import models
from userapp.models import Utilisateur
from formationapp.models import Formation

class Participation(models.Model):
    id_particip = models.AutoField(primary_key=True)
    date_particip = models.DateField(auto_now_add=True)
    id_user = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="participations")
    id_formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="participations")
