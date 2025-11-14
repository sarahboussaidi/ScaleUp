from django import forms
from .models import Stage

class StageForm(forms.ModelForm):
    class Meta:
        model = Stage
        # Remove 'entreprise' from fields
        fields = [
            'titre',
            'description',
            'localisation',
            'duree',
            'date_publication',
            'type',
        ]

        labels = {
            'titre': 'Stage Title',
            'description': 'Stage Description',
            'localisation': 'Stage Localisation',
            'duree': 'Stage Duration (weeks)',
            'date_publication': 'Publication Date',
            'type': 'Stage Type',
        }

        widgets = {
            'titre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter the title of the stage'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the internship'
            }),
            'localisation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location'
            }),
            'duree': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Duration in weeks'
            }),
            'date_publication': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Stage type (e.g., Full-time, Summer, etc.)'
            }),
        }