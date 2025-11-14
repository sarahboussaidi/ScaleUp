from django import forms# type: ignore
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm# type: ignore
from .models import Utilisateur

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Utilisateur._meta.get_field('role').choices)

    class Meta:
        model = Utilisateur
        fields = ['username', 'email', 'password1', 'password2', 'role']

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")


