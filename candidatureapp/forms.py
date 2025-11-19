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
        widgets = {
            'id_candidat': forms.TextInput(attrs={'readonly': 'readonly', 'disabled': 'disabled'}),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self._user = user
        if user is not None:
            self.fields['id_candidat'].initial = getattr(user, 'pk', user)
            self.fields['id_candidat'].widget = forms.HiddenInput()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if getattr(self, '_user', None) is not None:
            instance.id_candidat = self._user
        if commit:
            instance.save()
        return instance