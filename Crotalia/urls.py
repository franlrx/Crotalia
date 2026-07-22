from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # La ruta nativa de Django para tu panel de administrador
    path('admin/', admin.site.urls),
    
    # Conectamos las rutas de nuestra aplicación ganaderia
    # Al dejar las comillas vacías (''), las rutas cargarán directamente en la raíz de tu dominio
    path('', include('ganaderia.urls')),
]