from django.db import models
from django.contrib.auth.models import User
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
    
class Pedido(models.Model):

    TIPOS = (
        ('Local', 'En sitio'),
        ('Domicilio', 'A domicilio'),
    )

    cliente = models.ForeignKey(Perfil, on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
        
    def calcular_total(self):
     total = sum(detalle.subtotal() for detalle in self.detalles.all())
     return total

    def aplicar_puntos(self):
        puntos_ganados = int(self.total)
        perfil = self.cliente
        perfil.puntos += puntos_ganados
        perfil.actualizar_nivel()
        perfil.save()
        
        
        
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