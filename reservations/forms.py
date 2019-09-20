from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Reservations

class ReservationForm(forms.ModelForm):
    class Meta:
        model= Reservations
        fields= [
            'confirmation_code',
            'host',
            'guest',
            'check_in',
            'check_out',
            'price',
            'limekee_fee',
            'cleaning_fee',
        ]
