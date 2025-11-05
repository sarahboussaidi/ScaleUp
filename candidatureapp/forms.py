from django import forms
from .models import Candidature

class CandidatureForm(forms.ModelForm):
    class Meta:
        model = Candidature
        fields = [
            'id_candidat',
            'id_stage',
            'id_freelance',
            'id_formation',
            'cv_joint',
            'lettre_motivation',
            'statut',
        ]
