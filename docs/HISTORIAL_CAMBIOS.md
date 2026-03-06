# Historial de cambios (resumen)

## Base funcional

- [NUEVO] Se exige autenticacion para acciones de carrito: agregar productos y ver carrito ahora redirigen a `login` con mensaje informativo si el usuario no ha iniciado sesion.
- [NUEVO] Se agrego recurso de imagen `media/productos/Perro.jpg` para catalogo de productos.
- [NUEVO] Checkout y confirmacion muestran puntos estimados/acreditados calculados con la regla real de fidelizacion (evita mostrar el total del pedido como puntos).

## Interfaz (actualizacion reciente)

- [NUEVO] Se incorporo franja de marca "Restaurante Premium" en login, carrito, checkout, confirmacion y perfil de cliente para mayor consistencia visual.
- [NUEVO] Checkout y carrito muestran mensajes de fidelizacion visibles (badges) para reforzar acumulacion de puntos en el flujo de compra.
- [NUEVO] Perfil de cliente incluye bloque explicativo de fidelizacion: conversion de consumo a puntos, niveles (Bronce/Plata/Oro/VIP) y beneficios por nivel.
- [NUEVO] Rebranding de nombre visible del restaurante a "Antojopolis" en vistas principales y PDF.
- [NUEVO] Se movio el acceso al carrito al encabezado superior (navbar) para reducir friccion con la navegacion lateral.
- [NUEVO] Se aumento el tamano tipografico de la vista de perfil para mejorar legibilidad.

## PDF (actualizacion reciente)

- [NUEVO] La carta PDF agrega columna de foto por producto y estilos para miniaturas (`imagen-plato`), mejorando lectura visual del menu exportado.
- [NUEVO] Se ajusto el ancho de la columna de precio en PDF para equilibrar mejor la tabla al mostrar imagen + descripcion.

## Nota tecnica

- [VALIDO] Se detectan cambios en archivos compilados `__pycache__/*.pyc` en varios modulos del proyecto, consistentes con ejecucion local reciente.

- Carta publica con filtros, carrito y checkout.
- Carta mejorada con selector de cantidad al agregar productos.
- Carrito mejorado con actualizar cantidad y quitar items.
- Integracion de menu premium con boton para agregar al carrito local.
- Perfiles de cliente con puntos, niveles y promociones.
- Perfil con avatar personalizable y avatar por defecto (DiceBear).

## Fidelizacion

- Ruleta por eventos (registro y primer pedido).
- Ruleta mejorada con premios claros (porcentaje, puntos y giro extra) e indicador mas claro de resultado.
- Beneficios automaticos por compras acumuladas: cada $100,000 otorga giro extra y descuento 10%.
- Ajuste de conversion de puntos por compra: 1 punto por cada 2,000 de consumo.
- Ajuste de umbrales de nivel para balancear progresion: Plata (150), Oro (450), VIP (900).
- Normalizacion de oportunidades antiguas para evitar acumulacion excesiva de giros por error previo.
- Nuevo comando de mantenimiento `normalizar_fidelizacion` para limpiar giros/bonos legacy en lote.
- Ranking de clientes por actividad/consumo.
- Panel de gestion para otorgar premios (puntos o descuento).

## Checkout

- Modal preventivo para usuarios nuevos con giro de bienvenida pendiente antes de confirmar pago.

## Admin y gestion

- Acciones masivas en `/admin` para convertir/quitar superusuario.
- Edicion directa de `is_staff`, `is_superuser` y `is_active` en lista de usuarios.
- Vistas propias para crear, editar y eliminar productos sin depender de `/admin`.

## Seguridad y acceso

- Registro migrado a captcha checkbox tipo "No soy un robot" (reCAPTCHA v2) y validacion de correo unico.
- Login por correo + contrasena.
- Separacion de flujo admin vs cliente:
  - Admin no participa en fidelizacion.
  - Admin redirige a panel de gestion.

## Mapa y ubicacion

- Captura de ubicacion con Leaflet/OpenStreetMap en perfil y carrito.
- Busqueda de direccion con Nominatim para centrar automaticamente el mapa al escribir una direccion.

## Integracion externa temporal

- Vista separada `menu-api-temporal/` para probar consumo de Spoonacular.
- Se muestran recetas con imagen, descripcion y precio por porcion cuando la API devuelve datos.
- Se agrego respaldo automatico con DummyJSON cuando Spoonacular no responde o no tiene API key.
- Se agrego respaldo local final para mantener la vista operativa incluso sin conexion externa.

## Interfaz

- Se rediseño la navegacion lateral estilo panel izquierdo fijo de alto completo (referencia tipo Gmail).
- Sidebar auto-colapsable por hover/focus (reposo en iconos y expansion al pasar el mouse).
- Se agrego submenu de catalogos con "Carta local" y "Comida premium extranjera".
- El carrito en navegacion muestra contador de unidades y resumen de items distintos.
- Se agregaron controles +/- para cantidades en carta y carrito.
- Se mejoro uso del espacio en vistas con contenedor mas amplio y perfil reestructurado en dashboard de 2 columnas + tarjetas de resumen.
- Se agregaron tooltips y microanimaciones al sidebar retraido para mejorar navegacion rapida.
- Se rediseñaron vistas de checkout, confirmacion y ranking con tarjetas de resumen y mejor aprovechamiento del ancho.
- Ajuste visual general a estilo mas minimalista y limpio.
- Podio del ranking escalonado por altura (1ro, 2do, 3ro).

## PDF

- Carta PDF rediseñada (cabecera, categorias destacadas y formato tabular limpio).
- La carta ahora se abre en vista previa modal y permite descarga opcional.
- Se habilito framing same-origin para evitar bloqueo del iframe en la vista previa local.

## Estilo general

- Ajuste visual global a linea minimalista: botones, cards y formularios con estilo mas limpio y consistente.
- Pulido adicional en login, registro, panel admin y formularios de gestion de productos.
- Carrito reestructurado en 2 columnas con bloque de resumen para mejor uso de espacio.

## Avatares

- Se agrego personalizacion de avatar por usuario (`avatar_estilo`, `avatar_semilla`) con proveedor DiceBear.
- Ranking y panel de gestion muestran avatar junto al nombre del cliente.
- Se habilito carga de foto propia de perfil (opcional), manteniendo disponibles los avatares generados por estilo/semilla.

## PDF

- Exportacion de carta por `xhtml2pdf`.
