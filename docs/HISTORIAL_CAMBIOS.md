# Historial de cambios (resumen)

## Base funcional

- Carta publica con filtros, carrito y checkout.
- Perfiles de cliente con puntos, niveles y promociones.

## Fidelizacion

- Ruleta por eventos (registro y primer pedido).
- Ranking de clientes por actividad/consumo.
- Panel de gestion para otorgar premios (puntos o descuento).

## Admin y gestion

- Acciones masivas en `/admin` para convertir/quitar superusuario.
- Edicion directa de `is_staff`, `is_superuser` y `is_active` en lista de usuarios.
- Vistas propias para crear, editar y eliminar productos sin depender de `/admin`.

## Seguridad y acceso

- Registro con captcha y validacion de correo unico.
- Login por correo + contrasena.
- Separacion de flujo admin vs cliente:
  - Admin no participa en fidelizacion.
  - Admin redirige a panel de gestion.

## Mapa y ubicacion

- Captura de ubicacion con Leaflet/OpenStreetMap en perfil y carrito.

## PDF

- Exportacion de carta por `xhtml2pdf`.
