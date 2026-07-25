from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Vaca, Parto, Inseminacion
from itertools import zip_longest
from django.shortcuts import render, redirect, get_object_or_404
from .forms import VacaForm, InseminacionForm
from datetime import date, timedelta

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
    
    # --- NUEVA LÓGICA DE FILTRADO (HACE X DÍAS) ---
    dias = request.GET.get('dias')
    
    if dias and dias.isdigit():
        dias_int = int(dias)
        # Calculamos qué día era hace X días
        fecha_limite = date.today() - timedelta(days=dias_int)
        # Filtramos las inseminaciones que sean mayores o iguales a esa fecha
        inseminaciones_autorizadas = inseminaciones_autorizadas.filter(fecha__gte=fecha_limite)
    
    contexto = {
        'inseminaciones': inseminaciones_autorizadas,
        'nombre_granja': granja_usuario.nombre,
        'dias_seleccionados': dias # Lo enviamos para que el desplegable recuerde qué elegimos
    }
    return render(request, 'ganaderia/lista_inseminaciones.html', contexto)

@login_required(login_url='/admin/login/')
def lista_estimaciones(request):
    granja_usuario = request.user.perfil.granja
    estimaciones = Inseminacion.objects.filter(vaca__granja=granja_usuario, estado='POSITIVO')
    
    nombres_meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    datos_por_mes = {}

    # 1. Agrupamos los datos por mes y año como hacíamos antes
    for est in estimaciones:
        if est.estimacion_secado:
            clave_mes = (est.estimacion_secado.year, est.estimacion_secado.month)
            if clave_mes not in datos_por_mes:
                # Añadimos un valor 'value' (Ej: "2026-07") para usarlo en el filtro HTML
                datos_por_mes[clave_mes] = {'titulo': f"{nombres_meses[clave_mes[1]]} {clave_mes[0]}", 'secados': [], 'partos': [], 'value': f"{clave_mes[0]}-{clave_mes[1]:02d}"}
            datos_por_mes[clave_mes]['secados'].append(est)
            
        if est.estimacion_parto:
            clave_mes = (est.estimacion_parto.year, est.estimacion_parto.month)
            if clave_mes not in datos_por_mes:
                datos_por_mes[clave_mes] = {'titulo': f"{nombres_meses[clave_mes[1]]} {clave_mes[0]}", 'secados': [], 'partos': [], 'value': f"{clave_mes[0]}-{clave_mes[1]:02d}"}
            datos_por_mes[clave_mes]['partos'].append(est)

    # 2. Extraemos la lista de meses disponibles ANTES de aplicar cualquier filtro para el menú desplegable
    opciones_meses = [{'value': v['value'], 'titulo': v['titulo']} for k, v in sorted(datos_por_mes.items())]

    # 3. Comprobamos si el usuario ha seleccionado un mes en el filtro
    mes_filtro = request.GET.get('mes')
    if mes_filtro:
        try:
            year_f, month_f = map(int, mes_filtro.split('-'))
            # Si el mes filtrado existe en nuestros datos, nos quedamos solo con ese
            if (year_f, month_f) in datos_por_mes:
                datos_por_mes = {(year_f, month_f): datos_por_mes[(year_f, month_f)]}
            else:
                datos_por_mes = {}
        except ValueError:
            pass

    # 4. Ordenamos internamente los datos del mes (o meses) resultantes
    for clave in datos_por_mes:
        secados_ordenados = sorted(datos_por_mes[clave]['secados'], key=lambda x: x.estimacion_secado)
        partos_ordenados = sorted(datos_por_mes[clave]['partos'], key=lambda x: x.estimacion_parto)
        datos_por_mes[clave]['filas'] = list(zip_longest(secados_ordenados, partos_ordenados, fillvalue=None))

    claves_ordenadas = sorted(datos_por_mes.keys())
    estimaciones_agrupadas = [datos_por_mes[k] for k in claves_ordenadas]

    return render(request, 'ganaderia/lista_estimaciones.html', {
        'estimaciones_agrupadas': estimaciones_agrupadas,
        'opciones_meses': opciones_meses,
        'mes_seleccionado': mes_filtro
    })

# VISTA PARA CREAR VACA (Por ahora solo cargará la pantalla)
def crear_vaca(request):
    if request.method == 'POST':
        form = VacaForm(request.POST)
        if form.is_valid():
            vaca = form.save(commit=False)
            vaca.granja = request.user.perfil.granja
            vaca.save()
            return redirect('ganaderia:lista_vacas')
    else:
        form = VacaForm()
        form.fields['madre'].queryset = Vaca.objects.filter(granja=request.user.perfil.granja)

    # ¡ESTA ES LA LÍNEA CLAVE QUE TE FALTABA! El diccionario {'form': form} es el que envía los datos al HTML
    return render(request, 'ganaderia/crear_vaca.html', {'form': form})

# VISTA PARA ELIMINAR VACA
def eliminar_vaca(request, vaca_id):
    # Por seguridad, solo borramos si la petición llega por POST (al hacer clic en el botón)
    if request.method == 'POST':
        vaca = get_object_or_404(Vaca, id=vaca_id)
        vaca.delete()
    # Después de borrar, redirigimos automáticamente a la lista
    return redirect('ganaderia:lista_vacas')

# ==========================================
# GESTIÓN DE INSEMINACIONES
# ==========================================

@login_required(login_url='/admin/login/')
def crear_inseminacion(request):
    if request.method == 'POST':
        form = InseminacionForm(request.POST)
        if form.is_valid():
            inseminacion = form.save(commit=False)
            # La vaca ya pertenece a la granja, por lo que no necesitamos asignar la granja directamente a la inseminación
            inseminacion.save()
            return redirect('ganaderia:lista_inseminaciones')
    else:
        form = InseminacionForm()
        # Filtramos el desplegable para que solo salgan las vacas de tu granja
        form.fields['vaca'].queryset = Vaca.objects.filter(granja=request.user.perfil.granja)

    return render(request, 'ganaderia/crear_inseminacion.html', {'form': form})


@login_required(login_url='/admin/login/')
def actualizar_estado_inseminacion(request, inseminacion_id, nuevo_estado):
    if request.method == 'POST':
        # Buscamos la inseminación asegurándonos de que es de una vaca de esta granja (por seguridad)
        inseminacion = get_object_or_404(Inseminacion, id=inseminacion_id, vaca__granja=request.user.perfil.granja)
        
        if nuevo_estado == 'NEGATIVO':
            # Si fracasa, borramos el registro para mantener la base de datos limpia
            inseminacion.delete()
        elif nuevo_estado == 'POSITIVO':
            # Si es éxito, cambiamos el estado. Al hacer .save(), tu archivo models.py 
            # calculará automáticamente las fechas de secado y parto.
            inseminacion.estado = 'POSITIVO'
            inseminacion.save() 
            
    return redirect('ganaderia:lista_inseminaciones')