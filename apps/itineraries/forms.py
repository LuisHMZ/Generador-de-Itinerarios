from django import forms
from .models import TouristicPlace, Category

class TouristicPlaceForm(forms.ModelForm):
    class Meta:
        model = TouristicPlace
        fields = [
            'name', 'categories', 'description', 'address', 
            'lat', 'long', 'website', 'phone_number', 'opening_hours'
            # Omitimos external_api_id y rating porque esos se llenan solos o por la API
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Museo Soumaya'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle, Número, Ciudad...'}),
            'lat': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Ej. 19.4326'}),
            'long': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'Ej. -99.1332'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+52...'}),
            'opening_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Lun-Vie: 9am-6pm...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'categories': forms.CheckboxSelectMultiple(), # Muestra todas las categorías como checkboxes
        }
        
        labels = {
            'name': 'Nombre del Lugar',
            'categories': 'Categorías',
            'description': 'Descripción',
            'address': 'Dirección',
            'lat': 'Latitud',
            'long': 'Longitud',
            'website': 'Sitio Web',
            'phone_number': 'Teléfono',
            'opening_hours': 'Horario de Apertura'
        }