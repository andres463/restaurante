from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import DetallePedido, OportunidadRuleta, Pedido, Perfil, PremioCliente, Promocion


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.action(description='Dar permisos de administrador (staff + superusuario)')
def convertir_en_admin(modeladmin, request, queryset):
    queryset.update(is_staff=True, is_superuser=True, is_active=True)


@admin.action(description='Quitar permisos de administrador')
def quitar_admin(modeladmin, request, queryset):
    queryset.update(is_staff=False, is_superuser=False)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'is_staff',
        'is_superuser',
        'is_active',
        'last_login',
    )
    list_editable = ('is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    actions = [convertir_en_admin, quitar_admin]


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "puntos", "nivel", "fecha_registro")
    search_fields = ("usuario__username", "usuario__first_name", "usuario__last_name")
    list_filter = ("nivel", "fecha_registro")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cliente",
        "fecha",
        "tipo",
        "total",
        "descuento_aplicado",
        "promocion_aplicada",
        "completado",
    )
    list_filter = ("tipo", "completado", "fecha")
    search_fields = ("cliente__usuario__username",)
    date_hierarchy = "fecha"


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "producto", "cantidad")
    search_fields = ("producto__nombre",)


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "nivel_minimo", "descuento_porcentaje", "activa")
    list_filter = ("nivel_minimo", "activa")
    search_fields = ("titulo", "descripcion")


@admin.register(OportunidadRuleta)
class OportunidadRuletaAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'accion', 'usada', 'premio', 'puntos_otorgados', 'creada_en')
    list_filter = ('accion', 'usada')
    search_fields = ('perfil__usuario__username', 'premio')


@admin.register(PremioCliente)
class PremioClienteAdmin(admin.ModelAdmin):
    list_display = (
        'perfil',
        'tipo',
        'descripcion',
        'puntos',
        'descuento_porcentaje',
        'activo',
        'usado',
        'creado_en',
    )
    list_filter = ('tipo', 'activo', 'usado')
    search_fields = ('perfil__usuario__username', 'descripcion')
