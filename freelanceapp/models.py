from django.db import models
from userapp.models import Entreprise 
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
    id_entreprise=models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name="freelances", null=True)
     
    def _str_ (self):
        return self.titre_mission