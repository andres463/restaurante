# Instalacion y ejecucion

## 1) Requisitos

- Python 3.13
- Git

## 2) Clonar y entrar al proyecto

```bash
git clone <url-del-repo>
cd restaurante
```

## 3) Crear y activar entorno virtual

Windows (PowerShell):

```bash
python -m venv venv
venv\Scripts\activate
```

## 4) Instalar dependencias

```bash
pip install -r requirements.txt
```

## 5) Migraciones

```bash
python manage.py migrate
```

## 6) Cargar productos de ejemplo (opcional)

```bash
python manage.py poblar_carta --cantidad 80
python manage.py asignar_imagenes --limite 120
```

## 7) Crear superusuario (si no existe)

```bash
python manage.py createsuperuser
```

## 8) Ejecutar servidor

```bash
python manage.py runserver
```

## 9) Flujo recomendado para tu companero al hacer pull

Cuando reciba tus cambios por Git, no es solo "pull y listo". Debe ejecutar:

```bash
git pull
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Si no instala dependencias nuevas o no aplica migraciones, pueden aparecer errores de modulos faltantes o de base de datos.
