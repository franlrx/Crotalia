from django import forms
from .models import Vaca, Inseminacion

class VacaForm(forms.ModelForm):
    class Meta:
        model = Vaca
        # No incluimos 'granja' porque se la asignaremos automáticamente por detrás
        fields = ['numero_casa', 'crotal', 'nombre_padre', 'madre', 'fecha_nacimiento']
        
        # Le decimos a Django que el campo de fecha use el calendario del navegador
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

class InseminacionForm(forms.ModelForm):
    class Meta:
        model = Inseminacion
        fields = ['fecha', 'vaca', 'toro'] # Solo pedimos esto. El estado nace como DUDOSO automáticamente.
        widgets = {
            # Esto hace que en el navegador salga el calendario desplegable al pinchar
            'fecha': forms.DateInput(attrs={'type': 'date'}), 
        }