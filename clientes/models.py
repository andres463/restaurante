from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from decimal import Decimal
from urllib.parse import quote

from carta.models import Producto

class Perfil(models.Model):

    NIVELES = (
        ('Bronce', 'Bronce'),
        ('Plata', 'Plata'),
        ('Oro', 'Oro'),
        ('VIP', 'VIP'),
    )

    MONTO_POR_PUNTO = Decimal('2000')
    UMBRAL_PLATA = 150
    UMBRAL_ORO = 450
    UMBRAL_VIP = 900

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    puntos = models.IntegerField(default=0)
    nivel = models.CharField(max_length=10, choices=NIVELES, default='Bronce')
    direccion = models.CharField(max_length=255, blank=True)
    avatar_estilo = models.CharField(max_length=30, default='initials')
    avatar_semilla = models.CharField(max_length=120, blank=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.usuario.username

    def actualizar_nivel(self):
        if self.puntos >= self.UMBRAL_VIP:
            self.nivel = 'VIP'
        elif self.puntos >= self.UMBRAL_ORO:
            self.nivel = 'Oro'
        elif self.puntos >= self.UMBRAL_PLATA:
            self.nivel = 'Plata'
        else:
            self.nivel = 'Bronce'

    @property
    def avatar_url(self):
        estilos_validos = {
            'initials',
            'avataaars',
            'bottts',
            'identicon',
            'adventurer',
            'pixel-art',
        }
        estilo = self.avatar_estilo if self.avatar_estilo in estilos_validos else 'initials'
        semilla = (self.avatar_semilla or self.usuario.username or f'user-{self.usuario_id}').strip()
        return f"https://api.dicebear.com/8.x/{estilo}/svg?seed={quote(semilla)}"

    def aplicar_bonos_por_compras(self):
        total_compras = sum(
            (pedido.total for pedido in self.pedido_set.filter(completado=True).only('total')),
            Decimal('0.00'),
        )
        tramo_compra = Decimal('100000')
        tramos_logrados = int(total_compras // tramo_compra)

        tramos_otorgados = self.oportunidades_ruleta.filter(
            accion__startswith='bonus_compra_100k_',
        ).count()

        if tramos_logrados <= tramos_otorgados:
            return

        for bloque in range(tramos_otorgados + 1, tramos_logrados + 1):
            OportunidadRuleta.objects.get_or_create(
                perfil=self,
                accion=f'bonus_compra_100k_{bloque}',
            )
            PremioCliente.objects.create(
                perfil=self,
                tipo='DESCUENTO',
                descripcion='Bono por compras acumuladas: 10% en tu siguiente pedido',
                descuento_porcentaje=10,
                activo=True,
                usado=False,
            )


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
        return f"{self.perfil.usuario.username} - {self.accion_legible()}"

    def accion_legible(self):
        if self.accion == 'registro':
            return 'Registro de cuenta'
        if self.accion == 'primer_pedido':
            return 'Primer pedido completado'
        if self.accion.startswith('bonus_compra_100k_'):
            return 'Bono por compras acumuladas (100k)'
        if self.accion.startswith('extra_spin_'):
            return 'Giro extra ganado'
        return self.accion


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
        puntos_ganados = int(self.total / self.cliente.MONTO_POR_PUNTO)
        perfil = self.cliente
        perfil.puntos += puntos_ganados
        perfil.actualizar_nivel()
        perfil.save()
        perfil.aplicar_bonos_por_compras()

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
