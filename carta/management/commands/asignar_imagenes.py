from urllib.parse import quote
from urllib.request import urlopen

from django.db.models import Q
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from carta.models import Producto


class Command(BaseCommand):
    help = 'Descarga imagenes de internet y las asigna a productos sin imagen.'

    def add_arguments(self, parser):
        parser.add_argument('--limite', type=int, default=120, help='Maximo de productos a procesar')
        parser.add_argument('--forzar', action='store_true', help='Reemplaza imagenes existentes')

    def handle(self, *args, **options):
        limite = max(1, options['limite'])
        forzar = options['forzar']

        queryset = Producto.objects.all().order_by('id')
        if not forzar:
            queryset = queryset.filter(Q(imagen__isnull=True) | Q(imagen=''))

        productos = list(queryset[:limite])
        if not productos:
            self.stdout.write(self.style.WARNING('No hay productos pendientes de imagen.'))
            return

        exitos = 0
        errores = 0

        for producto in productos:
            termino = quote(producto.nombre.replace(' ', '-').lower())
            url = f'https://loremflickr.com/640/480/food?lock={producto.id}{termino}'

            try:
                with urlopen(url, timeout=25) as response:
                    contenido = response.read()

                nombre_archivo = f'producto_{producto.id}.jpg'
                producto.imagen.save(nombre_archivo, ContentFile(contenido), save=True)
                exitos += 1
            except Exception:
                errores += 1

        self.stdout.write(self.style.SUCCESS(f'Imagenes asignadas: {exitos}'))
        if errores:
            self.stdout.write(self.style.WARNING(f'Fallos al descargar: {errores}'))
