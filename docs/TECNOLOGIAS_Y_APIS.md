# Tecnologias, dependencias y APIs

## Framework base

- Django 6.0.3
- SQLite (desarrollo)

## Dependencias principales

- `Pillow`: manejo de imagenes.
- `django-simple-captcha`: captcha visual en registro.
- `xhtml2pdf`: exportacion de carta en PDF.

Instalacion:

```bash
pip install -r requirements.txt
```

## APIs / servicios externos usados

### 1) Mapas y ubicacion

- Libreria frontend: Leaflet
- Tiles: OpenStreetMap
- Uso: guardar latitud/longitud y direccion del cliente en perfil/carrito.

Nota: no requiere API key en la implementacion actual.

### 2) Imagenes de productos de ejemplo

- Fuente temporal para semillas visuales: `loremflickr.com`
- Uso por comando de gestion: `asignar_imagenes`.

Nota: estas imagenes son de apoyo para prototipo; para produccion se recomienda contenido propio/licenciado.

## Integraciones internas

- Ruleta y fidelizacion: app `clientes`
- Carrito/carta: app `carta`
- Checkout: app `pedidos`
