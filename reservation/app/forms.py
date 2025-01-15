from django import forms
from .models import Reservation
from django.core.exceptions import ValidationError

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['resource', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        resource = cleaned_data.get('resource')

        if start_time and end_time and start_time >= end_time:
            raise ValidationError("L'heure de début doit être antérieure à l'heure de fin.")

        # Vérifier la disponibilité de la ressource
        if resource and start_time and end_time:
            overlapping_reservations = Reservation.objects.filter(
                resource=resource,
                start_time__lt=end_time,
                end_time__gt=start_time,
                status='Reserved'
            ).exists()
            if overlapping_reservations:
                raise ValidationError("La ressource n'est pas disponible pour ce créneau.")

        return cleaned_data

