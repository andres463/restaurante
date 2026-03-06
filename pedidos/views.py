from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render

from clientes.models import DetallePedido, Pedido, PremioCliente, Promocion
from carta.models import Producto


NIVEL_ORDEN = {'Bronce': 1, 'Plata': 2, 'Oro': 3, 'VIP': 4}


def obtener_promocion_para_perfil(perfil):
    promociones_vigentes = [promo for promo in Promocion.objects.all() if promo.es_vigente()]
    promociones_validas = [
        promo
        for promo in promociones_vigentes
        if NIVEL_ORDEN.get(perfil.nivel, 0) >= NIVEL_ORDEN.get(promo.nivel_minimo, 0)
    ]
    if not promociones_validas:
        return None
    return max(promociones_validas, key=lambda promo: promo.descuento_porcentaje)


@login_required
def checkout(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.info(request, 'Las cuentas administrativas no realizan compras en el sistema de fidelizacion.')
        return redirect('panel_gestion')

    carrito = request.session.get("carrito", {})
    if not carrito:
        return redirect("lista_productos")

    productos = []
    total = Decimal("0.00")

    for producto_id, cantidad in carrito.items():
        producto = Producto.objects.get(id=producto_id)
        subtotal = producto.precio * cantidad
        total += subtotal
        productos.append(
            {
                "producto": producto,
                "cantidad": cantidad,
                "subtotal": subtotal,
            }
        )

    puntos_estimados_checkout = int(total / request.user.perfil.MONTO_POR_PUNTO)

    if request.method == "POST":
        tipo = request.POST.get("tipo")

        perfil = request.user.perfil
        pedido = Pedido.objects.create(cliente=perfil, tipo=tipo, completado=False)

        for item in productos:
            DetallePedido.objects.create(
                pedido=pedido,
                producto=item["producto"],
                cantidad=item["cantidad"],
            )

        promocion = obtener_promocion_para_perfil(perfil)
        premio_descuento = (
            PremioCliente.objects.filter(
                perfil=perfil,
                tipo='DESCUENTO',
                activo=True,
                usado=False,
            )
            .order_by('-descuento_porcentaje', '-creado_en')
            .first()
        )

        porcentaje_total = 0
        if promocion:
            porcentaje_total += promocion.descuento_porcentaje
        if premio_descuento:
            porcentaje_total += premio_descuento.descuento_porcentaje
        if porcentaje_total > 80:
            porcentaje_total = 80

        descuento = Decimal('0.00')
        if porcentaje_total > 0:
            descuento = (pedido.total * Decimal(porcentaje_total) / Decimal('100')).quantize(Decimal('0.01'))

        pedido.total = pedido.total - descuento
        pedido.descuento_aplicado = descuento
        pedido.promocion_aplicada = promocion

        puntos_estimados_confirmacion = int(pedido.total / perfil.MONTO_POR_PUNTO)

        # Una vez calculado el total final, marcamos como completado
        pedido.completado = True
        pedido.save(update_fields=['total', 'descuento_aplicado', 'promocion_aplicada', 'completado'])

        if premio_descuento:
            premio_descuento.usado = True
            premio_descuento.activo = False
            premio_descuento.save(update_fields=['usado', 'activo'])

        # Limpiar carrito
        request.session["carrito"] = {}

        return render(
            request,
            "pedidos/confirmacion.html",
            {
                "pedido": pedido,
                "productos": productos,
                "total": pedido.total,
                'descuento_aplicado': descuento,
                'promocion_aplicada': promocion,
                'premio_descuento': premio_descuento,
                'porcentaje_descuento_total': porcentaje_total,
                'puntos_estimados': puntos_estimados_confirmacion,
            },
        )

    return render(
        request,
        "pedidos/checkout.html",
        {
            "productos": productos,
            "total": total,
            "puntos_estimados": puntos_estimados_checkout,
            "tiene_giro_bienvenida_pendiente": request.user.perfil.oportunidades_ruleta.filter(
                accion='registro',
                usada=False,
            ).exists(),
        },
    )
