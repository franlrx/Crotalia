from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Vaca, Parto, Inseminacion
from itertools import zip_longest
from django.shortcuts import render, redirect, get_object_or_404
from .forms import VacaForm, InseminacionForm, PartoForm
from datetime import date, timedelta

# ==========================================
# PANTALLA PRINCIPAL Y BUSCADOR
# ==========================================
@login_required(login_url='/login/')
def inicio(request):
    return render(request, 'ganaderia/inicio.html')

@login_required(login_url='/login/')
def buscar_vaca(request):
    granja_usuario = request.user.perfil.granja
    query = request.GET.get('q') 
    resultados = Vaca.objects.filter(granja=granja_usuario, numero_casa__icontains=query)
    return render(request, 'ganaderia/resultados_busqueda.html', {'vacas': resultados, 'query': query})

# ==========================================
# LISTAS DE DATOS (AISLADAS POR GRANJA)
# ==========================================
@login_required(login_url='/login/')
def lista_vacas(request):
    granja_usuario = request.user.perfil.granja
    vacas_autorizadas = Vaca.objects.filter(granja=granja_usuario).order_by('-fecha_nacimiento')
    
    contexto = {
        'vacas': vacas_autorizadas,
        'nombre_granja': granja_usuario.nombre
    }
    return render(request, 'ganaderia/lista_vacas.html', contexto)

@login_required(login_url='/login/')
def lista_partos(request):
    granja_usuario = request.user.perfil.granja
    partos_autorizados = Parto.objects.filter(madre__granja=granja_usuario).order_by('-fecha_real')
    
    contexto = {
        'partos': partos_autorizados,
        'nombre_granja': granja_usuario.nombre
    }
    return render(request, 'ganaderia/lista_partos.html', contexto)

@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def lista_estimaciones(request):
    granja_usuario = request.user.perfil.granja
    estimaciones = Inseminacion.objects.filter(vaca__granja=granja_usuario, estado='POSITIVO')
    partos_registrados = Parto.objects.filter(madre__granja=granja_usuario)
    
    nombres_meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    datos_por_mes = {}

    # 1. Agrupamos los datos de Inseminaciones (Secados y Partos)
    for est in estimaciones:
        if est.estimacion_secado:
            clave_mes = (est.estimacion_secado.year, est.estimacion_secado.month)
            if clave_mes not in datos_por_mes:
                datos_por_mes[clave_mes] = {'titulo': f"{nombres_meses[clave_mes[1]]} {clave_mes[0]}", 'secados': [], 'partos': [], 'destetes': [], 'value': f"{clave_mes[0]}-{clave_mes[1]:02d}"}
            datos_por_mes[clave_mes]['secados'].append(est)
            
        if est.estimacion_parto:
            clave_mes = (est.estimacion_parto.year, est.estimacion_parto.month)
            if clave_mes not in datos_por_mes:
                datos_por_mes[clave_mes] = {'titulo': f"{nombres_meses[clave_mes[1]]} {clave_mes[0]}", 'secados': [], 'partos': [], 'destetes': [], 'value': f"{clave_mes[0]}-{clave_mes[1]:02d}"}
            datos_por_mes[clave_mes]['partos'].append(est)

    # 2. Agrupamos los datos de Partos Reales (Destetes: Fecha real + 60 días)
    for parto in partos_registrados:
        if parto.fecha_real:
            fecha_destete = parto.fecha_real + timedelta(days=60)
            clave_mes = (fecha_destete.year, fecha_destete.month)
            if clave_mes not in datos_por_mes:
                datos_por_mes[clave_mes] = {'titulo': f"{nombres_meses[clave_mes[1]]} {clave_mes[0]}", 'secados': [], 'partos': [], 'destetes': [], 'value': f"{clave_mes[0]}-{clave_mes[1]:02d}"}
            
            # Guardamos la fecha de destete calculada temporalmente en el objeto parto para usarla en el HTML
            parto.fecha_destete = fecha_destete
            datos_por_mes[clave_mes]['destetes'].append(parto)

    # 3. Menú desplegable para los filtros
    opciones_meses = [{'value': v['value'], 'titulo': v['titulo']} for k, v in sorted(datos_por_mes.items())]

    # 4. Filtro por mes
    mes_filtro = request.GET.get('mes')
    if mes_filtro:
        try:
            year_f, month_f = map(int, mes_filtro.split('-'))
            if (year_f, month_f) in datos_por_mes:
                datos_por_mes = {(year_f, month_f): datos_por_mes[(year_f, month_f)]}
            else:
                datos_por_mes = {}
        except ValueError:
            pass

    # 5. Ordenar las 3 listas internamente y emparejarlas en filas
    for clave in datos_por_mes:
        secados_ordenados = sorted(datos_por_mes[clave]['secados'], key=lambda x: x.estimacion_secado)
        partos_ordenados = sorted(datos_por_mes[clave]['partos'], key=lambda x: x.estimacion_parto)
        destetes_ordenados = sorted(datos_por_mes[clave]['destetes'], key=lambda x: x.fecha_destete)
        
        # zip_longest ahora alinea las 3 columnas
        datos_por_mes[clave]['filas'] = list(zip_longest(secados_ordenados, partos_ordenados, destetes_ordenados, fillvalue=None))

    claves_ordenadas = sorted(datos_por_mes.keys())
    estimaciones_agrupadas = [datos_por_mes[k] for k in claves_ordenadas]

    return render(request, 'ganaderia/lista_estimaciones.html', {
        'estimaciones_agrupadas': estimaciones_agrupadas,
        'opciones_meses': opciones_meses,
        'mes_seleccionado': mes_filtro
    })

# VISTA PARA CREAR VACA (Por ahora solo cargará la pantalla)
@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def editar_vaca(request, vaca_id):
    # Recuperamos la vaca asegurándonos de que pertenece a la granja del usuario
    vaca = get_object_or_404(Vaca, id=vaca_id, granja=request.user.perfil.granja)
    
    if request.method == 'POST':
        # Le pasamos el 'instance=vaca' para que Django sepa que estamos actualizando, no creando
        form = VacaForm(request.POST, instance=vaca)
        if form.is_valid():
            form.save()
            return redirect('ganaderia:lista_vacas')
    else:
        # Cargamos el formulario con los datos actuales de la vaca
        form = VacaForm(instance=vaca)
        
        # Filtramos las posibles madres: Solo vacas de esta granja y EXCLUIMOS a la propia vaca 
        # para que no puedas poner por error que una vaca es madre de sí misma
        form.fields['madre'].queryset = Vaca.objects.filter(granja=request.user.perfil.granja).exclude(id=vaca.id)

    return render(request, 'ganaderia/editar_vaca.html', {'form': form, 'vaca': vaca})

# VISTA PARA ELIMINAR VACA
@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
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


@login_required(login_url='/login/')
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

@login_required(login_url='/login/')
def crear_parto(request):
    if request.method == 'POST':
        form = PartoForm(request.POST)
        if form.is_valid():
            # El método save() del modelo Parto ya se encarga de crear la cría en el censo
            # si es hembra, por lo que aquí solo necesitamos guardarlo de forma normal.
            parto = form.save(commit=False)
            parto.save()
            return redirect('ganaderia:lista_partos')
    else:
        form = PartoForm()
        # Filtramos para que en el desplegable de madres solo salgan las vacas de tu granja
        form.fields['madre'].queryset = Vaca.objects.filter(granja=request.user.perfil.granja)

    return render(request, 'ganaderia/crear_parto.html', {'form': form})

@login_required(login_url='/login/')
def buscar_vaca(request):
    granja_usuario = request.user.perfil.granja
    query = request.GET.get('q', '') 
    
    if query:
        # Cambiamos '__icontains' por '__iexact' para forzar la coincidencia exacta
        resultados = Vaca.objects.filter(
            granja=granja_usuario, 
            numero_casa__iexact=query
        ).prefetch_related('inseminaciones', 'partos').order_by('numero_casa')
    else:
        resultados = None

    return render(request, 'ganaderia/resultados_busqueda.html', {'vacas': resultados, 'query': query})

@login_required(login_url='/login/')
def inicio(request):
    granja_usuario = request.user.perfil.granja
    
    # 1. Total de vacas activas en la granja
    total_vacas = Vaca.objects.filter(granja=granja_usuario).count()
    
    # 2. Tasa de éxito de inseminaciones
    total_inseminaciones = Inseminacion.objects.filter(vaca__granja=granja_usuario).count()
    inseminaciones_positivas = Inseminacion.objects.filter(vaca__granja=granja_usuario, estado='POSITIVO').count()
    
    if total_inseminaciones > 0:
        # Calculamos el porcentaje y lo redondeamos a 1 decimal
        tasa_exito = round((inseminaciones_positivas / total_inseminaciones) * 100, 1)
    else:
        tasa_exito = 0
        
    # 3. Partos esperados para el mes actual
    hoy = date.today()
    partos_este_mes = Inseminacion.objects.filter(
        vaca__granja=granja_usuario,
        estado='POSITIVO',
        estimacion_parto__year=hoy.year,
        estimacion_parto__month=hoy.month
    ).count()

    contexto = {
        'nombre_granja': granja_usuario.nombre,
        'total_vacas': total_vacas,
        'tasa_exito': tasa_exito,
        'partos_este_mes': partos_este_mes,
    }
    
    return render(request, 'ganaderia/inicio.html', contexto)