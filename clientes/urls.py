from django.urls import path

from .views import (
    girar_ruleta,
    guardar_ubicacion,
    mi_perfil,
    otorgar_premio,
    panel_gestion,
    ranking_clientes,
    registro_exitoso,
    registro_usuario,
)

urlpatterns = [
    path("mi-perfil/", mi_perfil, name="mi_perfil"),
    path('registro/', registro_usuario, name='registro_usuario'),
    path('registro/exitoso/', registro_exitoso, name='registro_exitoso'),
    path('ruleta/girar/', girar_ruleta, name='girar_ruleta'),
    path('ranking/', ranking_clientes, name='ranking_clientes'),
    path('panel-gestion/', panel_gestion, name='panel_gestion'),
    path('otorgar-premio/<int:perfil_id>/', otorgar_premio, name='otorgar_premio'),
    path('guardar-ubicacion/', guardar_ubicacion, name='guardar_ubicacion'),
]

