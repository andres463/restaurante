from django.shortcuts import render
from .models import Producto, Categoria
from django.shortcuts import redirect
from decimal import Decimal


def lista_productos(request):
    categoria_id = request.GET.get('categoria')
    buscar = request.GET.get('buscar')

    productos = Producto.objects.filter(disponible=True)

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    if buscar:
        productos = productos.filter(nombre__icontains=buscar)

    categorias = Categoria.objects.all()

    return render(request, 'carta/lista_productos.html', {
        'productos': productos,
        'categorias': categorias
    })
    


def agregar_al_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})

    if str(producto_id) in carrito:
        carrito[str(producto_id)] += 1
    else:
        carrito[str(producto_id)] = 1

    request.session['carrito'] = carrito
    return redirect('lista_productos')


def ver_carrito(request):
    from .models import Producto

    carrito = request.session.get('carrito', {})
    productos = []
    total = Decimal('0.00')

    for producto_id, cantidad in carrito.items():
        producto = Producto.objects.get(id=producto_id)
        subtotal = producto.precio * cantidad
        total += subtotal

        productos.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal
        })

    return render(request, 'carta/carrito.html', {
        'productos': productos,
        'total': total
    })