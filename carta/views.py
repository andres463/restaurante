from decimal import Decimal
from collections import defaultdict
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
from django.views.decorators.clickjacking import xframe_options_sameorigin

from clientes.models import Promocion
from .forms import ProductoForm
from .models import Producto, Categoria


def _consumir_json(url, headers=None, timeout=12):
    request_api = Request(url, headers=headers or {'Accept': 'application/json'})
    with urlopen(request_api, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def _fallback_dummyjson():
    payload = _consumir_json('https://dummyjson.com/recipes?limit=12')
    productos = []
    for item in payload.get('recipes', []):
        descripcion = ''
        instrucciones = item.get('instructions') or []
        if instrucciones:
            descripcion = instrucciones[0]
        if not descripcion:
            descripcion = f"{item.get('cuisine', 'Cocina internacional')} - Dificultad {item.get('difficulty', 'Media')}"

        calorias = item.get('caloriesPerServing')
        precio = None
        if calorias is not None:
            try:
                estimado = max(6, min(45, float(calorias) / 18))
                precio = Decimal(str(estimado)).quantize(Decimal('0.01'))
            except Exception:
                precio = None

        productos.append(
                {
                    'nombre': item.get('name', 'Sin nombre'),
                    'descripcion': str(descripcion)[:180] + ('...' if len(str(descripcion)) > 180 else ''),
                    'precio': precio,
                    'imagen': item.get('image'),
                    'fuente': '',
                }
            )
    return productos


def _fallback_local_estatico():
    return [
        {
            'nombre': 'Classic Margherita Pizza',
            'descripcion': 'Pizza italiana clasica con salsa de tomate, mozzarella y albahaca fresca.',
            'precio': Decimal('12.90'),
            'imagen': 'https://cdn.dummyjson.com/recipe-images/1.webp',
            'fuente': 'https://dummyjson.com/recipes/1',
        },
        {
            'nombre': 'Chicken Alfredo Pasta',
            'descripcion': 'Pasta cremosa con pollo salteado, ajo y parmesano.',
            'precio': Decimal('14.40'),
            'imagen': 'https://cdn.dummyjson.com/recipe-images/4.webp',
            'fuente': 'https://dummyjson.com/recipes/4',
        },
        {
            'nombre': 'Quinoa Salad with Avocado',
            'descripcion': 'Ensalada ligera de quinoa con aguacate, tomate cherry y aderezo de limon.',
            'precio': Decimal('10.20'),
            'imagen': 'https://cdn.dummyjson.com/recipe-images/6.webp',
            'fuente': 'https://dummyjson.com/recipes/6',
        },
        {
            'nombre': 'Beef and Broccoli Stir-Fry',
            'descripcion': 'Salteado asiatico de res con brocoli en salsa de soya.',
            'precio': Decimal('13.80'),
            'imagen': 'https://cdn.dummyjson.com/recipe-images/8.webp',
            'fuente': 'https://dummyjson.com/recipes/8',
        },
        {
            'nombre': 'Shrimp Scampi Pasta',
            'descripcion': 'Pasta con camarones, ajo, limon y toque de vino blanco.',
            'precio': Decimal('15.30'),
            'imagen': 'https://cdn.dummyjson.com/recipe-images/10.webp',
            'fuente': 'https://dummyjson.com/recipes/10',
        },
        {
            'nombre': 'Mango Lassi',
            'descripcion': 'Bebida cremosa y refrescante de mango, yogur y cardamomo.',
            'precio': Decimal('6.50'),
            'imagen': 'https://cdn.dummyjson.com/recipe-images/22.webp',
            'fuente': 'https://dummyjson.com/recipes/22',
        },
    ]


def menu_api_temporal(request):
    api_key = settings.SPOONACULAR_API_KEY
    productos_api = []
    error_api = ''
    fuente_api = 'Spoonacular'

    if api_key:
        params = urlencode(
            {
                'number': 12,
                'addRecipeInformation': 'true',
                'sort': 'popularity',
            }
        )
        url = f'https://api.spoonacular.com/recipes/complexSearch?{params}'

        try:
            payload = _consumir_json(url, headers={'x-api-key': api_key, 'Accept': 'application/json'})

            for item in payload.get('results', []):
                resumen_limpio = strip_tags(item.get('summary', '')).strip()
                precio_cents = item.get('pricePerServing')
                precio = None
                if precio_cents is not None:
                    try:
                        precio = (Decimal(str(precio_cents)) / Decimal('100')).quantize(Decimal('0.01'))
                    except Exception:
                        precio = None

                productos_api.append(
                    {
                        'nombre': item.get('title', 'Sin nombre'),
                        'descripcion': resumen_limpio[:180] + ('...' if len(resumen_limpio) > 180 else ''),
                        'precio': precio,
                        'imagen': item.get('image'),
                        'fuente': item.get('sourceUrl', ''),
                    }
                )
        except HTTPError as error:
            error_api = f'Error de Spoonacular ({error.code}). Cargamos un menu de respaldo temporal.'
        except URLError:
            error_api = 'No se pudo conectar a Spoonacular. Cargamos un menu de respaldo temporal.'
        except Exception:
            error_api = 'Ocurrio un error consultando Spoonacular. Cargamos un menu de respaldo temporal.'
    else:
        error_api = 'No hay clave de Spoonacular configurada. Mostramos un menu externo de respaldo para seguir probando.'

    if not productos_api:
        fuente_api = 'DummyJSON (respaldo)'
        try:
            productos_api = _fallback_dummyjson()
        except Exception:
            productos_api = _fallback_local_estatico()
            fuente_api = 'Catalogo local de respaldo'
            error_api = 'No hubo conexion a APIs externas. Mostramos un respaldo local para que la vista siga operativa.'

    return render(
        request,
        'carta/menu_api_temporal.html',
        {
            'productos_api': productos_api,
            'error_api': error_api,
            'fuente_api': fuente_api,
        },
    )


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
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para agregar productos al carrito.')
        return redirect('login')

    if request.method != 'POST':
        return redirect('lista_productos')

    producto = get_object_or_404(Producto, id=producto_id, disponible=True)
    carrito = request.session.get("carrito", {})
    cantidad = request.POST.get('cantidad', '1')

    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        cantidad = 1

    cantidad = max(1, min(20, cantidad))

    if str(producto_id) in carrito:
        carrito[str(producto_id)] += cantidad
    else:
        carrito[str(producto_id)] = cantidad

    request.session["carrito"] = carrito
    messages.success(request, f'Se agregaron {cantidad} x {producto.nombre} al carrito.')
    return redirect("lista_productos")


@require_POST
def agregar_premium_al_carrito(request):
    nombre = request.POST.get('nombre', '').strip()[:150]
    descripcion = request.POST.get('descripcion', '').strip()[:1200]
    precio = request.POST.get('precio', '').strip()

    if not nombre or not precio:
        messages.error(request, 'No se pudo agregar el producto premium.')
        return redirect('menu_api_temporal')

    try:
        precio_decimal = Decimal(precio).quantize(Decimal('0.01'))
    except Exception:
        messages.error(request, 'El precio del producto premium no es valido.')
        return redirect('menu_api_temporal')

    categoria, _ = Categoria.objects.get_or_create(nombre='Comida premium extranjera')
    producto, creado = Producto.objects.get_or_create(
        nombre=nombre,
        categoria=categoria,
        defaults={
            'descripcion': descripcion or 'Producto temporal importado desde menu externo.',
            'precio': precio_decimal,
            'disponible': True,
        },
    )

    if not creado:
        producto.descripcion = descripcion or producto.descripcion
        producto.precio = precio_decimal
        producto.disponible = True
        producto.save(update_fields=['descripcion', 'precio', 'disponible'])

    carrito = request.session.get("carrito", {})
    carrito[str(producto.id)] = carrito.get(str(producto.id), 0) + 1
    request.session["carrito"] = carrito
    messages.success(request, f'{producto.nombre} agregado al carrito.')
    return redirect('ver_carrito')


def actualizar_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('ver_carrito')

    carrito = request.session.get('carrito', {})
    if str(producto_id) not in carrito:
        return redirect('ver_carrito')

    cantidad = request.POST.get('cantidad', '1')
    try:
        cantidad = int(cantidad)
    except (TypeError, ValueError):
        cantidad = 1

    if cantidad <= 0:
        carrito.pop(str(producto_id), None)
    else:
        carrito[str(producto_id)] = min(20, cantidad)

    request.session['carrito'] = carrito
    return redirect('ver_carrito')


def quitar_del_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('ver_carrito')

    carrito = request.session.get('carrito', {})
    carrito.pop(str(producto_id), None)
    request.session['carrito'] = carrito
    return redirect('ver_carrito')


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
    if not request.user.is_authenticated:
        messages.warning(request, 'Debes iniciar sesión para ver tu carrito.')
        return redirect('login')

    carrito = request.session.get("carrito", {})
    productos = []
    total = Decimal("0.00")

    for producto_id, cantidad in carrito.items():
        producto = Producto.objects.filter(id=producto_id, disponible=True).first()
        if not producto:
            continue
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


@xframe_options_sameorigin
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

    productos = Producto.objects.filter(disponible=True).select_related("categoria").order_by('categoria__nombre', 'nombre')
    agrupado = defaultdict(list)
    for producto in productos:
        categoria_nombre = producto.categoria.nombre if producto.categoria else 'Sin categoria'
        agrupado[categoria_nombre].append(producto)

    categorias = [
        {
            'nombre': nombre,
            'productos': items,
        }
        for nombre, items in agrupado.items()
    ]

    template = get_template("carta/carta_pdf.html")
    html = template.render(
        {
            "productos": productos,
            "categorias": categorias,
        }
    )

    response = HttpResponse(content_type="application/pdf")
    if request.GET.get('descargar') == '1':
        response["Content-Disposition"] = 'attachment; filename="carta_restaurante.pdf"'
    else:
        response["Content-Disposition"] = 'inline; filename="carta_restaurante.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error al generar el PDF de la carta.", status=500)

    return response
