from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Vaca, Parto, Inseminacion

# ==========================================
# 1. VISTA DE VACAS
# ==========================================
@login_required(login_url='/admin/login/')
def lista_vacas(request):
    granja_usuario = request.user.perfil.granja
    
    # Filtramos por la granja del usuario y ordenamos de más jóvenes a más viejas
    vacas_autorizadas = Vaca.objects.filter(granja=granja_usuario).order_by('-fecha_nacimiento')
    
    contexto = {
        'vacas': vacas_autorizadas,
        'nombre_granja': granja_usuario.nombre
    }
    return render(request, 'ganaderia/lista_vacas.html', contexto)

# ==========================================
# 2. VISTA DE PARTOS
# ==========================================
@login_required(login_url='/admin/login/')
def lista_partos(request):
    granja_usuario = request.user.perfil.granja
    
    # Usamos el doble guion bajo (madre__granja) para viajar a la tabla de Vaca y comprobar la granja
    partos_autorizados = Parto.objects.filter(madre__granja=granja_usuario).order_by('-fecha_real')
    
    contexto = {
        'partos': partos_autorizados,
        'nombre_granja': granja_usuario.nombre
    }
    return render(request, 'ganaderia/lista_partos.html', contexto)

# ==========================================
# 3. VISTA DE INSEMINACIONES
# ==========================================
@login_required(login_url='/admin/login/')
def lista_inseminaciones(request):
    granja_usuario = request.user.perfil.granja
    
    # Usamos el doble guion bajo (vaca__granja) para viajar a la tabla de Vaca y comprobar la granja
    inseminaciones_autorizadas = Inseminacion.objects.filter(vaca__granja=granja_usuario).order_by('-fecha')
    
    contexto = {
        'inseminaciones': inseminaciones_autorizadas,
        'nombre_granja': granja_usuario.nombre
    }
    return render(request, 'ganaderia/lista_inseminaciones.html', contexto)