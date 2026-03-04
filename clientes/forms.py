import re

from django import forms
from captcha.fields import CaptchaField
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class RegistroUsuarioForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label='Nombre completo')
    email = forms.EmailField(required=True, label='Correo electronico')
    captcha = CaptchaField(label='Verificacion humana')

    class Meta:
        model = User
        fields = ('first_name', 'email', 'password1', 'password2', 'captcha')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este correo ya esta registrado.')
        return email

    def _crear_username(self, nombre):
        base = re.sub(r'[^a-z0-9]+', '', nombre.lower().replace(' ', ''))[:12] or 'cliente'
        username = base
        secuencia = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{secuencia}"
            secuencia += 1
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        nombre = self.cleaned_data['first_name'].strip()
        email = self.cleaned_data['email'].strip().lower()
        user.first_name = nombre
        user.email = email
        user.username = self._crear_username(nombre)
        if commit:
            user.save()
        return user


class LoginUsuarioForm(AuthenticationForm):
    username = forms.EmailField(label='Correo electronico')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        email = self.cleaned_data.get('username', '').strip().lower()
        password = self.cleaned_data.get('password')

        if email and password:
            user = User.objects.filter(email=email).order_by('id').first()
            if user:
                self.cleaned_data['username'] = user.username

        return super().clean()
