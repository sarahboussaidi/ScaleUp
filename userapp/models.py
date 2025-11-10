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

"""
# ========================
# Load predefined skills and domains
# ========================ù
Open the Django shell:

    python manage.py shell


Paste this:

    from userapp.models import Domain, Skill

    domains_skills = {
        "Programming": ["Python", "C++", "Java", "JavaScript", "SQL"],
        "Design": ["Photoshop", "Illustrator", "Figma", "UI/UX"],
        "Marketing": ["Content Creation", "Social Media", "Email Marketing"],
        "Management": ["Leadership", "Teamwork", "Communication", "Planning"],
    }

    for domain_name, skills in domains_skills.items():
        domain, _ = Domain.objects.get_or_create(name=domain_name)
        for skill_name in skills:
            Skill.objects.get_or_create(domain=domain, name=skill_name)

    print("✅ Skills and domains added successfully.")
    print("Domains:", Domain.objects.count(), "Skills:", Skill.objects.count())


Then run:

    exit()


"""
# -----------------------------------------
# DOMAIN model 
# -----------------------------------------

class Domain(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

# -----------------------------------------
# SKILL model (linked to domain)
# -----------------------------------------

class Skill(models.Model):
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('domain', 'name')

    def __str__(self):
        return f"{self.name} ({self.domain.name})"

# -----------------------------------------
# CANDIDAT model (inherits from Utilisateur)
# -----------------------------------------

class Candidat(Utilisateur):
    age = models.PositiveIntegerField(blank=True, null=True)
    cv = models.FileField(upload_to='cv/', blank=True, null=True)
    skills = models.ManyToManyField(Skill, blank=True)
    class Meta:
        verbose_name = "Candidat"

    def __str__(self):
        return f"Candidat: {self.first_name} {self.last_name}"
