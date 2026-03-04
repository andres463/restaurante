from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.template.loader import get_template

from clientes.models import Promocion
from .forms import ProductoForm
from .models import Producto, Categoria


def lista_productos(request):
    categoria_id = request.GET.get("categoria")
    buscar = request.GET.get("buscar")

    productos = Producto.objects.filter(disponible=True)

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    if buscar:
        productos = productos.filter(nombre__icontains=buscar)

    categorias = Categoria.objects.all()

    promociones = [
        promo
        for promo in Promocion.objects.all()
        if promo.es_vigente()
    ]

    return render(
        request,
        "carta/lista_productos.html",
        {
            "productos": productos,
            "categorias": categorias,
            "promociones": promociones,
        },
    )


def agregar_al_carrito(request, producto_id):
    carrito = request.session.get("carrito", {})

    if str(producto_id) in carrito:
        carrito[str(producto_id)] += 1
    else:
        carrito[str(producto_id)] = 1

    request.session["carrito"] = carrito
    return redirect("lista_productos")


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado correctamente a la carta.')
            return redirect('lista_productos')
    else:
        form = ProductoForm()

    return render(request, 'carta/crear_producto.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('lista_productos')
    else:
        form = ProductoForm(instance=producto)

    return render(
        request,
        'carta/editar_producto.html',
        {
            'form': form,
            'producto': producto,
        },
    )


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado correctamente.')
        return redirect('lista_productos')

    return render(
        request,
        'carta/eliminar_producto.html',
        {
            'producto': producto,
        },
    )


def ver_carrito(request):
    carrito = request.session.get("carrito", {})
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

    perfil = None
    if request.user.is_authenticated:
        perfil = getattr(request.user, 'perfil', None)

    return render(
        request,
        "carta/carrito.html",
        {
            "productos": productos,
            "total": total,
            'perfil': perfil,
        },
    )


def carta_pdf(request):
    """
    Genera una versión en PDF de la carta actual.

    Para un funcionamiento completo se recomienda instalar xhtml2pdf:
        pip install xhtml2pdf
    """
    try:
        from xhtml2pdf import pisa
    except ImportError:
        return HttpResponse(
            "La generación de PDF requiere instalar el paquete 'xhtml2pdf'.",
            status=500,
        )

    productos = Producto.objects.filter(disponible=True).select_related("categoria")
    categorias = Categoria.objects.all()

    template = get_template("carta/carta_pdf.html")
    html = template.render(
        {
            "productos": productos,
            "categorias": categorias,
        }
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="carta_restaurante.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error al generar el PDF de la carta.", status=500)

    return response
