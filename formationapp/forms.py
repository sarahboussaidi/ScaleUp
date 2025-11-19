from django import forms
from .models import Formation, lesson

class FormationForm(forms.ModelForm):
    class Meta:
        model = Formation
        fields = ['titre', 'description', 'niveau', 'categorie', 'duree', 'certif', 'id_user', 'image']
        labels = {
            'titre': 'Titre de la formation',
            'description': 'Description',
            'niveau': 'Niveau',
            'categorie': 'Catégorie',
            'duree': 'Durée (en heures)',
            'certif': 'Certification disponible',
            'id_user': 'Formateur',
            'image': 'Image de la formation',
        }
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'input-style mb-20'}),
            'description': forms.Textarea(attrs={'class': 'input-style mb-20', 'rows': 4}),
            'niveau': forms.Select(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'duree': forms.NumberInput(attrs={'class': 'input-style mb-20'}),
            'certif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'id_user': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),

        }
class LessonForm(forms.ModelForm):
        class Meta:
            model = lesson
            fields = ['titre', 'contenu', 'file']  
            labels = {
                'titre': 'Titre de la leçon',
                'contenu': 'Contenu',
                'file': 'Fichier joint',
            }
            widgets = {
                'titre': forms.TextInput(attrs={'class': 'input-style mb-20'}),
                'contenu': forms.Textarea(attrs={'class': 'input-style mb-20', 'rows': 6}),
                'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            }