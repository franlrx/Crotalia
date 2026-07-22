from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Vaca, Parto, Inseminacion
from itertools import zip_longest

# ==========================================
# PANTALLA PRINCIPAL Y BUSCADOR
# ==========================================
@login_required(login_url='/admin/login/')
def inicio(request):
    return render(request, 'ganaderia/inicio.html')

@login_required(login_url='/admin/login/')
def buscar_vaca(request):
    granja_usuario = request.user.perfil.granja
    query = request.GET.get('q') 
    resultados = Vaca.objects.filter(granja=granja_usuario, numero_casa__icontains=query)
    return render(request, 'ganaderia/resultados_busqueda.html', {'vacas': resultados, 'query': query})

# ==========================================
# LISTAS DE DATOS (AISLADAS POR GRANJA)
# ==========================================
@login_required(login_url='/admin/login/')
def lista_vacas(request):
    granja_usuario = request.user.perfil.granja
    vacas_autorizadas = Vaca.objects.filter(granja=granja_usuario).order_by('-fecha_nacimiento')
    
    contexto = {
        'vacas': vacas_autorizadas,
        'nombre_granja': granja_usuario.nombre
    }
    return render(request, 'ganaderia/lista_vacas.html', contexto)

@login_required(login_url='/admin/login/')
def lista_partos(request):
    granja_usuario = request.user.perfil.granja
    partos_autorizados = Parto.objects.filter(madre__granja=granja_usuario).order_by('-fecha_real')
    
    contexto = {
        'partos': partos_autorizados,
        'nombre_granja': granja_usuario.nombre
    }
    return render(request, 'ganaderia/lista_partos.html', contexto)

@login_required(login_url='/admin/login/')
def lista_inseminaciones(request):
    granja_usuario = request.user.perfil.granja
    inseminaciones_autorizadas = Inseminacion.objects.filter(vaca__granja=granja_usuario).order_by('-fecha')
    
    contexto = {
        'inseminaciones': inseminaciones_autorizadas,
        'nombre_granja': granja_usuario.nombre
    }
    return render(request, 'ganaderia/lista_inseminaciones.html', contexto)

# ==========================================
# CALENDARIO DE ESTIMACIONES AGRUPADO
# ==========================================
@login_required(login_url='/admin/login/')
def lista_estimaciones(request):
    granja_usuario = request.user.perfil.granja
    estimaciones = Inseminacion.objects.filter(vaca__granja=granja_usuario, estado='POSITIVO')
    
    nombres_meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    datos_por_mes = {}

    for est in estimaciones:
        if est.estimacion_secado:
            clave_mes = (est.estimacion_secado.year, est.estimacion_secado.month)
            if clave_mes not in datos_por_mes:
                datos_por_mes[clave_mes] = {'titulo': f"{nombres_meses[clave_mes[1]]} {clave_mes[0]}", 'secados': [], 'partos': []}
            datos_por_mes[clave_mes]['secados'].append(est)
            
        if est.estimacion_parto:
            clave_mes = (est.estimacion_parto.year, est.estimacion_parto.month)
            if clave_mes not in datos_por_mes:
                datos_por_mes[clave_mes] = {'titulo': f"{nombres_meses[clave_mes[1]]} {clave_mes[0]}", 'secados': [], 'partos': []}
            datos_por_mes[clave_mes]['partos'].append(est)

    for clave in datos_por_mes:
        secados_ordenados = sorted(datos_por_mes[clave]['secados'], key=lambda x: x.estimacion_secado)
        partos_ordenados = sorted(datos_por_mes[clave]['partos'], key=lambda x: x.estimacion_parto)
        datos_por_mes[clave]['filas'] = list(zip_longest(secados_ordenados, partos_ordenados, fillvalue=None))

    claves_ordenadas = sorted(datos_por_mes.keys())
    estimaciones_agrupadas = [datos_por_mes[k] for k in claves_ordenadas]

    return render(request, 'ganaderia/lista_estimaciones.html', {'estimaciones_agrupadas': estimaciones_agrupadas})