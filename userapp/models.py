from django.db import models
from django.contrib.auth.models import AbstractUser


# ========================
# CLASSE DE BASE : UTILISATEUR
# ========================
class Utilisateur(AbstractUser):
    """
    Classe de base représentant tous les types d'utilisateurs :
    Admin, Entreprise et Candidat.
    """
    email = models.EmailField(unique=True)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(upload_to='photos/', blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Admin'),
            ('entreprise', 'Entreprise'),
            ('candidat', 'Candidat'),
        ],
        default='candidat'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.role})"

    # --- Méthodes générales de gestion de profil ---
    def inscrire(self):
        pass

    def se_connecter(self, email, mot_de_passe):
        pass

    def modifier_profil(self):
        pass

    def supprimer_compte(self):
        self.delete()

    def consulter_profil(self):
        return self


# ========================
# CLASSE ADMIN
# ========================
class Admin(Utilisateur):
    """
    Représente un administrateur de la plateforme.
    Hérite des attributs de Utilisateur.
    """
    niveau_acces = models.CharField(max_length=50, default='standard')

    class Meta:
        verbose_name = "Administrateur"

    def __str__(self):
        return f"Admin: {self.username}"

    # --- Méthodes spécifiques au rôle admin ---
    def consulter_offres(self):
        pass

    def consulter_candidatures(self):
        pass


# ========================
# CLASSE ENTREPRISE
# ========================
class Entreprise(Utilisateur):
    """
    Représente une entreprise qui peut publier des offres et organiser des formations.
    """
    nom_entreprise = models.CharField(max_length=100)
    domaine = models.CharField(max_length=100)
    site_web = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Entreprise"

    def __str__(self):
        return f"Entreprise: {self.nom_entreprise}"


# ========================
# CLASSE CANDIDAT
# ========================
class Candidat(Utilisateur):
    """
    Représente un utilisateur normal qui cherche un stage, une mission ou une formation.
    """
    age = models.PositiveIntegerField(blank=True, null=True)
    cv = models.FileField(upload_to='cv/', blank=True, null=True)

    class Meta:
        verbose_name = "Candidat"

    def __str__(self):
        return f"Candidat: {self.first_name} {self.last_name}"
