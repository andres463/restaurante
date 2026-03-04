import random
from decimal import Decimal
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import RegistroUsuarioForm
from .models import OportunidadRuleta, Pedido, Perfil, PremioCliente, Promocion


def registro_usuario(request):
    if request.user.is_authenticated:
        return redirect('lista_productos')

    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            messages.success(
                request,
                'Cuenta creada con exito. Ya tienes un giro de bienvenida en la ruleta.',
            )
            return redirect('mi_perfil')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'clientes/registro.html', {'form': form})


@login_required
def mi_perfil(request):
    if request.user.is_staff or request.user.is_superuser:
        messages.info(request, 'Tu cuenta es administrativa. Te redirigimos al panel de gestion.')
        return redirect('panel_gestion')

    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)

    pedidos = (
        Pedido.objects.filter(cliente=perfil)
        .order_by("-fecha")
    )

    total_gastado = sum(p.total for p in pedidos)
    total_pedidos = pedidos.count()

    promociones = [
        promo
        for promo in Promocion.objects.all()
        if promo.es_vigente()
    ]

    oportunidades_disponibles = perfil.oportunidades_ruleta.filter(usada=False)
    historial_ruleta = perfil.oportunidades_ruleta.filter(usada=True)[:5]
    premios = perfil.premios.filter(activo=True, usado=False)

    return render(
        request,
        "clientes/perfil.html",
        {
            "perfil": perfil,
            "pedidos": pedidos[:5],
            "total_gastado": total_gastado,
            "total_pedidos": total_pedidos,
            "promociones": promociones,
            "oportunidades_disponibles": oportunidades_disponibles,
            "historial_ruleta": historial_ruleta,
            'premios': premios,
        },
    )


@login_required
def ranking_clientes(request):
    periodo = request.GET.get('periodo', 'todo')
    fecha_desde = None
    if periodo == 'semana':
        fecha_desde = timezone.now() - timedelta(days=7)
    elif periodo == 'mes':
        fecha_desde = timezone.now() - timedelta(days=30)

    filtro_periodo = Q(pedido__completado=True)
    if fecha_desde:
        filtro_periodo &= Q(pedido__fecha__gte=fecha_desde)

    perfiles = (
        Perfil.objects.select_related('usuario')
        .annotate(
            pedidos_completados=Count('pedido', filter=filtro_periodo),
            total_consumido=Coalesce(Sum('pedido__total', filter=filtro_periodo), Value(Decimal('0.00'))),
        )
        .order_by('-total_consumido', '-pedidos_completados', '-puntos')[:20]
    )
    return render(request, 'clientes/ranking.html', {'perfiles': perfiles, 'periodo': periodo})


@login_required
def panel_gestion(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'No tienes permisos para entrar al panel de gestion.')
        return redirect('lista_productos')

    periodo = request.GET.get('periodo', 'todo')
    fecha_desde = None
    if periodo == 'semana':
        fecha_desde = timezone.now() - timedelta(days=7)
    elif periodo == 'mes':
        fecha_desde = timezone.now() - timedelta(days=30)

    filtro_periodo = Q(pedido__completado=True)
    if fecha_desde:
        filtro_periodo &= Q(pedido__fecha__gte=fecha_desde)

    perfiles = (
        Perfil.objects.select_related('usuario')
        .annotate(
            pedidos_completados=Count('pedido', filter=filtro_periodo),
            total_consumido=Coalesce(Sum('pedido__total', filter=filtro_periodo), Value(Decimal('0.00'))),
        )
        .order_by('-total_consumido', '-pedidos_completados', '-puntos')[:30]
    )

    return render(request, 'clientes/panel_gestion.html', {'perfiles': perfiles, 'periodo': periodo})


@login_required
@require_POST
def otorgar_premio(request, perfil_id):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('lista_productos')

    perfil = Perfil.objects.filter(id=perfil_id).first()
    if not perfil:
        messages.error(request, 'No se encontro el perfil seleccionado.')
        return redirect('panel_gestion')

    tipo = request.POST.get('tipo')

    if tipo == 'PUNTOS':
        puntos = int(request.POST.get('puntos', 0))
        if puntos <= 0:
            messages.error(request, 'Los puntos deben ser mayores a cero.')
            return redirect('panel_gestion')
        perfil.puntos += puntos
        perfil.actualizar_nivel()
        perfil.save()
        PremioCliente.objects.create(
            perfil=perfil,
            tipo='PUNTOS',
            descripcion=f'Premio administrativo de {puntos} puntos',
            puntos=puntos,
            activo=False,
            usado=True,
        )
        messages.success(request, f'Se otorgaron {puntos} puntos a {perfil.usuario.username}.')
    elif tipo == 'DESCUENTO':
        descuento = int(request.POST.get('descuento_porcentaje', 0))
        if descuento <= 0 or descuento > 80:
            messages.error(request, 'El descuento debe estar entre 1% y 80%.')
            return redirect('panel_gestion')
        PremioCliente.objects.create(
            perfil=perfil,
            tipo='DESCUENTO',
            descripcion=f'Descuento especial de {descuento}% para siguiente pedido',
            descuento_porcentaje=descuento,
            activo=True,
            usado=False,
        )
        messages.success(request, f'Se asigno descuento del {descuento}% a {perfil.usuario.username}.')
    else:
        messages.error(request, 'Tipo de premio no valido.')

    return redirect('panel_gestion')


@login_required
@require_POST
def girar_ruleta(request):
    perfil: Perfil = request.user.perfil
    oportunidad = perfil.oportunidades_ruleta.filter(usada=False).order_by('creada_en').first()

    if not oportunidad:
        return JsonResponse({'ok': False, 'error': 'No tienes giros disponibles.'}, status=400)

    premios = [
        ('10 puntos extra', 10),
        ('20 puntos extra', 20),
        ('30 puntos extra', 30),
        ('50 puntos extra', 50),
        ('Doble puntos en tu siguiente pedido', 40),
        ('Postre de cortesia', 25),
    ]
    indice = random.randint(0, len(premios) - 1)
    premio_texto, puntos = premios[indice]

    perfil.puntos += puntos
    perfil.actualizar_nivel()
    perfil.save()

    oportunidad.usada = True
    oportunidad.usada_en = timezone.now()
    oportunidad.premio = premio_texto
    oportunidad.puntos_otorgados = puntos
    oportunidad.save(update_fields=['usada', 'usada_en', 'premio', 'puntos_otorgados'])
    giros_restantes = perfil.oportunidades_ruleta.filter(usada=False).count()

    return JsonResponse(
        {
            'ok': True,
            'premio': premio_texto,
            'puntos': puntos,
            'segmento': indice,
            'puntos_totales': perfil.puntos,
            'nivel': perfil.nivel,
            'giros_restantes': giros_restantes,
        }
    )


@login_required
@require_POST
def guardar_ubicacion(request):
    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)
    latitud = request.POST.get('latitud')
    longitud = request.POST.get('longitud')
    direccion = request.POST.get('direccion', '').strip()

    if not latitud or not longitud:
        return JsonResponse({'ok': False, 'error': 'Latitud y longitud son obligatorias.'}, status=400)

    try:
        perfil.latitud = Decimal(latitud)
        perfil.longitud = Decimal(longitud)
    except Exception:
        return JsonResponse({'ok': False, 'error': 'Coordenadas invalidas.'}, status=400)

    perfil.direccion = direccion
    perfil.save(update_fields=['latitud', 'longitud', 'direccion'])

    return JsonResponse({'ok': True, 'direccion': perfil.direccion})
