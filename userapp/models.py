from django.db import models  # type: ignore
from django.contrib.auth.models import AbstractUser  # type: ignore
from django.db import transaction  # type: ignore

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

print("Skills and domains added successfully.")
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
"""
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
"""

# ========================
# CANDIDAT model (inherits from Utilisateur)
# ========================
class Candidat(models.Model):
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='candidat')
    age = models.PositiveIntegerField(blank=True, null=True)
    cv = models.FileField(upload_to='cv/', blank=True, null=True)
    skills = models.ManyToManyField(Skill, blank=True)
    # New fields
    portfolio_website = models.URLField(blank=True, null=True)
    years_experience = models.PositiveIntegerField(blank=True, null=True)
    education_level = models.CharField(
        max_length=50,
        choices=[
            ('High School', 'High School'),
            ('Bachelor', 'Bachelor'),
            ('Master', 'Master'),
            ('PhD', 'PhD'),
            ('Other', 'Other')
        ],
        blank=True,
        null=True
    )
    
    
    bio = models.TextField(blank=True, null=True)
    
    def get_education_choices(self):
        return self._meta.get_field('education_level').choices
    class Meta:
        verbose_name = "Candidat"

    def __str__(self):
        return f"Candidat: {self.user.first_name} {self.user.last_name}"

    def save(self, *args, **kwargs):
        #self.role = 'candidat'  # force role
        super().save(*args, **kwargs)




# ========================
# ENTREPRISE model adjustments
# ========================
class Entreprise(models.Model):
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='entreprise')
    nom_entreprise = models.CharField(max_length=100)
    domaine = models.CharField(max_length=100)
    site_web = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.CharField(max_length=255, null=True, blank=True)
    logo = models.ImageField(upload_to='entreprises/logos/', blank=True, null=True)  # <- new field

    class Meta:
        verbose_name = "Entreprise"

    def __str__(self):
        return f"Entreprise: {self.nom_entreprise}"

    def save(self, *args, **kwargs):
        #self.role = 'entreprise'  # force role
        super().save(*args, **kwargs)


# ========================
# ADMIN model adjustments
# ========================
class Admin(models.Model):
    user = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='admin')
    niveau_acces = models.CharField(max_length=50, default='standard')

    class Meta:
        verbose_name = "Administrateur"

    def __str__(self):
        return f"Admin: {self.user.username}"

    def save(self, *args, **kwargs):
        #self.role = 'admin'  # force role
        super().save(*args, **kwargs)




def change_user_role(user: Utilisateur, new_role: str):
    """
    Migrate a user to a new role (candidat, entreprise, admin)
    """

    common_fields = {
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "password": user.password,
        "adresse": user.adresse,
        "telephone": user.telephone,
        "photo": user.photo,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
    }

    with transaction.atomic():
        # Delete old subclass object
        old_role = user.role
        user_id = user.id
        user.delete()  # deletes multi-table row for old subclass

        # Create new object of the correct subclass
        if new_role == "candidat":
            new_user = Candidat.objects.create(**common_fields)
        elif new_role == "entreprise":
            new_user = Entreprise.objects.create(**common_fields)
        elif new_role == "admin":
            new_user = Admin.objects.create(**common_fields)
        else:
            raise ValueError("Unknown role")

        # Set the role field
        new_user.role = new_role
        new_user.save()

        return new_user



