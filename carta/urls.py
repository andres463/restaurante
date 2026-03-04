from django.urls import path

from .views import (
    agregar_al_carrito,
    carta_pdf,
    crear_producto,
    editar_producto,
    eliminar_producto,
    lista_productos,
    ver_carrito,
)

urlpatterns = [
    path("", lista_productos, name="lista_productos"),
    path("agregar/<int:producto_id>/", agregar_al_carrito, name="agregar_al_carrito"),
    path("carrito/", ver_carrito, name="ver_carrito"),
    path("carta-pdf/", carta_pdf, name="carta_pdf"),
    path('gestion/carta/nuevo/', crear_producto, name='crear_producto'),
    path('gestion/carta/<int:producto_id>/editar/', editar_producto, name='editar_producto'),
    path('gestion/carta/<int:producto_id>/eliminar/', eliminar_producto, name='eliminar_producto'),
]
