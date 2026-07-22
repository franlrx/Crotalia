from django.contrib import admin
from .models import Granja, PerfilGanadero,  Vaca, Inseminacion, Parto

# Registramos los modelos básicos
admin.site.register(Granja)
admin.site.register(PerfilGanadero)
admin.site.register(Vaca)
admin.site.register(Inseminacion)
admin.site.register(Parto)