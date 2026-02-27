from django.contrib import admin
from .models import Perfil
from .models import Pedido
from .models import DetallePedido

admin.site.register(Perfil)
admin.site.register(Pedido)
admin.site.register(DetallePedido)