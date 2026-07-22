from django.urls import path
from . import views

# Definimos el nombre de la aplicación para organizar bien las rutas internamente
app_name = 'ganaderia'

urlpatterns = [
    # Ruta para las vacas (Ej: 127.0.0.1:8000/vacas/)
    path('vacas/', views.lista_vacas, name='lista_vacas'),
    
    # Ruta para los partos (Ej: 127.0.0.1:8000/partos/)
    path('partos/', views.lista_partos, name='lista_partos'),
    
    # Ruta para las inseminaciones (Ej: 127.0.0.1:8000/inseminaciones/)
    path('inseminaciones/', views.lista_inseminaciones, name='lista_inseminaciones'),
]