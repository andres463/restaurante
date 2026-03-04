from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from carta.models import Producto

class Perfil(models.Model):

    NIVELES = (
        ('Bronce', 'Bronce'),
        ('Plata', 'Plata'),
        ('Oro', 'Oro'),
        ('VIP', 'VIP'),
    )

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    puntos = models.IntegerField(default=0)
    nivel = models.CharField(max_length=10, choices=NIVELES, default='Bronce')
    direccion = models.CharField(max_length=255, blank=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.usuario.username

    def actualizar_nivel(self):
        if self.puntos >= 600:
            self.nivel = 'VIP'
        elif self.puntos >= 300:
            self.nivel = 'Oro'
        elif self.puntos >= 100:
            self.nivel = 'Plata'
        else:
            self.nivel = 'Bronce'


class OportunidadRuleta(models.Model):
    ACCIONES = (
        ('registro', 'Registro de cuenta'),
        ('primer_pedido', 'Primer pedido completado'),
    )

    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='oportunidades_ruleta')
    accion = models.CharField(max_length=30, choices=ACCIONES)
    usada = models.BooleanField(default=False)
    premio = models.CharField(max_length=150, blank=True)
    puntos_otorgados = models.PositiveIntegerField(default=0)
    creada_en = models.DateTimeField(auto_now_add=True)
    usada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('perfil', 'accion')
        ordering = ('-creada_en',)

    def __str__(self):
        return f"{self.perfil.usuario.username} - {self.get_accion_display()}"


class PremioCliente(models.Model):
    TIPOS = (
        ('PUNTOS', 'Puntos extra'),
        ('DESCUENTO', 'Descuento en siguiente pedido'),
    )

    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name='premios')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descripcion = models.CharField(max_length=160)
    puntos = models.PositiveIntegerField(default=0)
    descuento_porcentaje = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    usado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-creado_en',)

    def __str__(self):
        return f"{self.perfil.usuario.username} - {self.descripcion}"


class Promocion(models.Model):
    NIVELES = Perfil.NIVELES

    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    nivel_minimo = models.CharField(
        max_length=10,
        choices=NIVELES,
        default='Bronce',
        help_text="Nivel mínimo del cliente para acceder a la promoción.",
    )
    descuento_porcentaje = models.PositiveIntegerField(
        help_text="Porcentaje de descuento aproximado que ofrece la promoción."
    )
    activa = models.BooleanField(default=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.titulo

    def es_vigente(self):
        from django.utils import timezone

        hoy = timezone.now().date()
        if self.fecha_inicio and hoy < self.fecha_inicio:
            return False
        if self.fecha_fin and hoy > self.fecha_fin:
            return False
        return self.activa


class Pedido(models.Model):

    TIPOS = (
        ('Local', 'En sitio'),
        ('Domicilio', 'A domicilio'),
    )

    cliente = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento_aplicado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promocion_aplicada = models.ForeignKey(
        'Promocion',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='pedidos_aplicados',
    )
    completado = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Verificar estado anterior
        if self.pk:
            pedido_anterior = Pedido.objects.get(pk=self.pk)
        else:
            pedido_anterior = None

        super().save(*args, **kwargs)

        # Si pasa de no completado a completado
        if self.completado and (not pedido_anterior or not pedido_anterior.completado):
            self.aplicar_puntos()
            self.crear_oportunidad_primer_pedido()
        
    def calcular_total(self):
     total = sum(detalle.subtotal() for detalle in self.detalles.all())
     return total

    def aplicar_puntos(self):
        puntos_ganados = int(self.total)
        perfil = self.cliente
        perfil.puntos += puntos_ganados
        perfil.actualizar_nivel()
        perfil.save()

    def crear_oportunidad_primer_pedido(self):
        total_completados = Pedido.objects.filter(cliente=self.cliente, completado=True).count()
        if total_completados == 1:
            OportunidadRuleta.objects.get_or_create(
                perfil=self.cliente,
                accion='primer_pedido',
            )
        
        
        
class DetallePedido(models.Model):

    pedido = models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)

    def subtotal(self):
        return self.producto.precio * self.cantidad

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        total = sum(det.subtotal() for det in self.pedido.detalles.all())
        self.pedido.total = total
        self.pedido.save(update_fields=['total'])

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
