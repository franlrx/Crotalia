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

    # Ruta para la página de inicio (Ej: 127.0.0.1:8000/inicio/)
    path('', views.inicio, name='inicio'), 

    # Ruta para la página de estimaciones (Ej: 127.0.0.1:8000/estimaciones/)
    path('estimaciones/', views.lista_estimaciones, name='lista_estimaciones'),

    # Ruta para la página de búsqueda de vacas (Ej: 127.0.0.1:8000/buscar/)
    path('buscar/', views.buscar_vaca, name='buscar_vaca'),

    path('vacas/crear/', views.crear_vaca, name='crear_vaca'),
    path('vacas/eliminar/<int:vaca_id>/', views.eliminar_vaca, name='eliminar_vaca'),

    # Rutas para crear y actualizar inseminaciones
    path('inseminaciones/crear/', views.crear_inseminacion, name='crear_inseminacion'),
    path('inseminaciones/estado/<int:inseminacion_id>/<str:nuevo_estado>/', views.actualizar_estado_inseminacion, name='actualizar_estado_inseminacion'),
]