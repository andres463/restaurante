import random

from django.core.management.base import BaseCommand

from carta.models import Categoria, Producto


class Command(BaseCommand):
    help = 'Crea alimentos de ejemplo en la carta (sin usuarios).'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=50, help='Cantidad de productos a crear')

    def handle(self, *args, **options):
        cantidad = max(1, options['cantidad'])

        categorias = [
            'Entradas',
            'Platos fuertes',
            'Postres',
            'Bebidas',
            'Especiales',
            'Comida rapida',
        ]

        bases = [
            'Arepa', 'Hamburguesa', 'Wrap', 'Pizza', 'Pasta', 'Ensalada', 'Sopa', 'Bowl',
            'Sandwich', 'Taco', 'Arroz', 'Pollo', 'Carne', 'Pescado', 'Limonada', 'Jugo',
            'Cheesecake', 'Brownie', 'Helado', 'Ceviche', 'Empanada', 'Patacon', 'Lasagna',
        ]

        adjetivos = [
            'de la casa', 'premium', 'criollo', 'campesino', 'artesanal', 'especial',
            'clasico', 'del huerto', 'a la parrilla', 'del chef', 'casero', 'supremo',
        ]

        ingredientes = [
            'queso', 'toque de ajo', 'chimichurri', 'salsa de la casa', 'vegetales frescos',
            'papas crocantes', 'arroz de coco', 'ensalada fresca', 'mayonesa artesanal',
            'salsa BBQ', 'guacamole', 'salsa picante suave', 'pan brioche', 'cebolla caramelizada',
        ]

        categorias_objs = []
        for nombre in categorias:
            categoria, _ = Categoria.objects.get_or_create(nombre=nombre)
            categorias_objs.append(categoria)

        creados = 0
        intentos = 0
        limite_intentos = cantidad * 5

        while creados < cantidad and intentos < limite_intentos:
            intentos += 1
            base = random.choice(bases)
            adjetivo = random.choice(adjetivos)
            nombre = f"{base} {adjetivo}"[:150]

            if Producto.objects.filter(nombre=nombre).exists():
                nombre = f"{nombre} {random.randint(1, 999)}"[:150]

            descripcion = f"Preparacion con {random.choice(ingredientes)} y {random.choice(ingredientes)}."
            precio = random.randint(12000, 65000)
            categoria = random.choice(categorias_objs)

            Producto.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                precio=precio,
                categoria=categoria,
                disponible=True,
            )
            creados += 1

        self.stdout.write(self.style.SUCCESS(f'Se crearon {creados} productos de ejemplo.'))
