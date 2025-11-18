from django.contrib import auth
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class Sujet(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    date_creation = models.DateTimeField(default=timezone.now)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    author = models.ForeignKey('userapp.Utilisateur', on_delete=models.CASCADE)

    def __str__(self):
        return self.titre

    def clean(self):
        super().clean()
        if self.date_creation and self.date_creation > timezone.now():
            raise ValidationError("La date de création ne peut pas être dans le futur.")
    
class Question(models.Model):
    sujet = models.ForeignKey(Sujet, related_name='questions', on_delete=models.CASCADE)
    texte = models.TextField()
    date_creation = models.DateTimeField(default=timezone.now)
    utilisateur = models.ForeignKey('userapp.Utilisateur', on_delete=models.CASCADE)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    

    def __str__(self):
        return self.texte[:50]
    def clean(self):
        super().clean()
        if self.date_creation and self.date_creation > timezone.now():
            raise ValidationError("La date de création ne peut pas être dans le futur.")

class Reponse(models.Model):
    question = models.ForeignKey(Question, related_name='reponses', on_delete=models.CASCADE)
    texte = models.TextField()
    date_creation = models.DateTimeField(default=timezone.now)
    utilisateur = models.ForeignKey('userapp.Utilisateur', on_delete=models.CASCADE)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)

    def __str__(self):
        return self.texte[:50]  # Affiche les 50 premiers caractères de la réponse

    def clean(self):
        super().clean()
        if self.date_creation and self.date_creation > timezone.now():
            raise ValidationError("La date de création ne peut pas être dans le futur.")

