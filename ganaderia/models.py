import datetime
import calendar
from django.db import models
from django.contrib.auth.models import User

# 1. EL NUEVO NÚCLEO: LA GRANJA
class Granja(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre de la Granja")
    fecha_registro = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nombre

# 2. VINCULAR USUARIOS A GRANJAS (El Perfil)
class PerfilGanadero(models.Model):
    # Conecta el sistema de login de Django con nuestro perfil
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    # Conecta a ese usuario con una granja específica
    granja = models.ForeignKey(Granja, on_delete=models.CASCADE, related_name='usuarios')

    def __str__(self):
        return f"Perfil de {self.usuario.username} - {self.granja.nombre}"

#3. MODELOS DE GANADERÍA
class Vaca(models.Model):

    # Relación con la granja a la que pertenece
    granja = models.ForeignKey(Granja, on_delete=models.CASCADE, related_name='vacas', verbose_name="Granja")

    # El número interno que usáis en casa. Lo pongo como CharField por si alguna vez usáis letras (ej: "12B")
    numero_casa = models.CharField(max_length=10, verbose_name="Nº Casa")
    
    # El crotal es único a nivel europeo (suele ser ES + 12 números), por lo que le ponemos unique=True
    crotal = models.CharField(max_length=14, unique=True, verbose_name="Crotal")
    
    # El padre. Le ponemos blank=True y null=True por si compráis una vaca y no sabéis quién es el padre
    nombre_padre = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre del Padre")

    # La madre. Le ponemos blank=True y null=True por si compráis una vaca y no sabéis quién es la madre
    madre = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, related_name='hijas', verbose_name="Madre")
    # La fecha de nacimiento
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento")

    class Meta:
        # ¡Regla de oro de bases de datos! Evita que existan dos vacas con el mismo número EN LA MISMA GRANJA
        unique_together = ('granja', 'numero_casa')

    # Esta función sirve para que cuando veas la base de datos, no ponga "Vaca Object", 
    # sino que te muestre algo fácil de leer como "12 - ES123456789012"
    def __str__(self):
        return f"Casa: {self.numero_casa} | Crotal: {self.crotal}"

class Inseminacion(models.Model):
    ESTADO_CHOICES = [
        ('POSITIVO', 'Positivo'),
        ('NEGATIVO', 'Negativo'),
        ('DUDOSO', 'Dudoso'),
    ]

    fecha = models.DateField(verbose_name="Fecha de Inseminación")
    vaca = models.ForeignKey(Vaca, on_delete=models.CASCADE, related_name='inseminaciones', verbose_name="Vaca (Nº Casa)")
    toro = models.CharField(max_length=100, verbose_name="Nombre del Toro")
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='DUDOSO', verbose_name="Estado")
    
    # Nuevos campos para las estimaciones (pueden quedar en blanco si la inseminación no es positiva)
    estimacion_secado = models.DateField(blank=True, null=True, verbose_name="Estimación de Secado")
    estimacion_parto = models.DateField(blank=True, null=True, verbose_name="Estimación de Parto")

    def __str__(self):
        return f"Inseminación {self.vaca.numero_casa} - {self.fecha} - Toro: {self.toro}"

    def save(self, *args, **kwargs):
        # Si el estado es Positivo y hay una fecha de inseminación registrada
        if self.estado == 'POSITIVO' and self.fecha:
            
            # --- CÁLCULO ESTIMACIÓN DE SECADO (7 meses) ---
            mes_secado = self.fecha.month - 1 + 7
            año_secado = self.fecha.year + (mes_secado // 12)
            mes_secado = (mes_secado % 12) + 1
            # Para evitar errores si el día original es 31 y el mes de destino solo tiene 30 días
            dia_secado = min(self.fecha.day, calendar.monthrange(año_secado, mes_secado)[1])
            self.estimacion_secado = datetime.date(año_secado, mes_secado, dia_secado)

            # --- CÁLCULO ESTIMACIÓN DE PARTO (9 meses) ---
            mes_parto = self.fecha.month - 1 + 9
            año_parto = self.fecha.year + (mes_parto // 12)
            mes_parto = (mes_parto % 12) + 1
            dia_parto = min(self.fecha.day, calendar.monthrange(año_parto, mes_parto)[1])
            self.estimacion_parto = datetime.date(año_parto, mes_parto, dia_parto)
            
        else:
            # Si el usuario cambia el estado de Positivo a Negativo/Dudoso por error,
            # limpiamos las estimaciones para que no queden fechas falsas guardadas.
            self.estimacion_secado = None
            self.estimacion_parto = None

        # Guardamos definitivamente en la base de datos
        super().save(*args, **kwargs)

class Parto(models.Model):
    GENERO_CHOICES = [
        ('MACHO', 'Macho'),
        ('HEMBRA', 'Hembra'),
    ]

    # Datos del parto
    fecha_real = models.DateField(verbose_name="Fecha Real del Parto")
    madre = models.ForeignKey(Vaca, on_delete=models.CASCADE, related_name='partos', verbose_name="Madre (Nº Casa)")
    nombre_padre = models.CharField(max_length=100, blank=True, null=True, verbose_name="Nombre del Padre")
    
    # Datos de la cría
    genero_cria = models.CharField(max_length=10, choices=GENERO_CHOICES, verbose_name="Género de la Cría")
    numero_casa_cria = models.CharField(max_length=10, blank=True, null=True, verbose_name="Nº Casa de la Cría (Solo hembras)")

    def __str__(self):
        return f"Parto de {self.madre.numero_casa} - {self.fecha_real} ({self.genero_cria})"

    # Interceptamos el guardado
    def save(self, *args, **kwargs):
        # 1. Corrección estricta: Si es macho, forzamos a que el número de casa sea nulo, 
        # sin importar si el usuario escribió algo en la pantalla.
        if self.genero_cria == 'MACHO':
            self.numero_casa_cria = None
            
        # 2. Ahora sí, guardamos el parto en la base de datos
        super().save(*args, **kwargs)
        
        # 3. Automatización (Solo si es hembra y tiene número)
        if self.genero_cria == 'HEMBRA' and self.numero_casa_cria:
            if not Vaca.objects.filter(numero_casa=self.numero_casa_cria, granja=self.madre.granja).exists():
                crotal_temporal = f"P{self.madre.granja.id}-{self.numero_casa_cria}"
                Vaca.objects.create(
                    granja=self.madre.granja,
                    numero_casa=self.numero_casa_cria,
                    crotal=crotal_temporal, 
                    nombre_padre=self.nombre_padre,
                    madre=self.madre,
                    fecha_nacimiento=self.fecha_real
                )