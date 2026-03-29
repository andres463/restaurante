
"""
Django settings for restaurante_fidelizacion project.
Configurado para despliegue en Render 🚀
"""

from pathlib import Path
import os
from django.core.management.utils import get_random_secret_key
import dj_database_url


def env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}

# ==============================
# 📁 RUTAS DEL PROYECTO
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================
# 🔐 SEGURIDAD
# ==============================

# SECRET_KEY:
# - En desarrollo usa una generada automáticamente
# - En producción (Render) usa la variable de entorno
SECRET_KEY = os.environ.get("SECRET_KEY") or get_random_secret_key()

# DEBUG:
# - True en local
# - False en Render automáticamente
DEBUG = 'RENDER' not in os.environ

# ALLOWED_HOSTS:
# - Permite el dominio que Render genera automáticamente
ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)


# ==============================
# 📦 APLICACIONES INSTALADAS
# ==============================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps del proyecto
    'carta',
    'clientes',
    'pedidos',

    # Librerías externas
    'django_recaptcha',
    'storages',
]


# ==============================
# ⚙️ MIDDLEWARE
# ==============================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # WhiteNoise permite servir archivos estáticos en producción
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ==============================
# 🌐 CONFIGURACIÓN GENERAL
# ==============================
ROOT_URLCONF = 'restaurante_fidelizacion.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # Carpeta de templates global
        'DIRS': [os.path.join(BASE_DIR, 'templates')],

        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                # Context processor personalizado
                'carta.context_processors.carrito_resumen',
            ],
        },
    },
]

WSGI_APPLICATION = 'restaurante_fidelizacion.wsgi.application'


# ==============================
# 🗄️ BASE DE DATOS
# ==============================
# - En local usa SQLite
# - En Render usa PostgreSQL automáticamente (DATABASE_URL)
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=not DEBUG
    )
}


# ==============================
# 🔑 VALIDACIÓN DE CONTRASEÑAS
# ==============================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        },
    },
]


# ==============================
# 🌍 INTERNACIONALIZACIÓN
# ==============================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ==============================
# 📁 ARCHIVOS ESTÁTICOS (CSS, JS)
# ==============================
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
        'OPTIONS': {
            'location': MEDIA_ROOT,
            'base_url': MEDIA_URL,
        },
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '').strip()
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '').strip()
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '').strip()
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', '').strip() or None
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', '').strip() or None
AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN', '').strip() or None
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = env_flag('AWS_QUERYSTRING_AUTH', default=True)
AWS_S3_FILE_OVERWRITE = False

USE_S3_MEDIA = bool(AWS_STORAGE_BUCKET_NAME) and (
    bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY) or env_flag('AWS_USE_IAM_ROLE', default=False)
)

if USE_S3_MEDIA:
    if not AWS_S3_CUSTOM_DOMAIN:
        if AWS_S3_ENDPOINT_URL:
            AWS_S3_CUSTOM_DOMAIN = AWS_S3_ENDPOINT_URL.replace('https://', '').replace('http://', '').rstrip('/')
        elif AWS_S3_REGION_NAME:
            AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
        else:
            AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'access_key': AWS_ACCESS_KEY_ID or None,
            'secret_key': AWS_SECRET_ACCESS_KEY or None,
            'bucket_name': AWS_STORAGE_BUCKET_NAME,
            'region_name': AWS_S3_REGION_NAME,
            'endpoint_url': AWS_S3_ENDPOINT_URL,
            'default_acl': AWS_DEFAULT_ACL,
            'querystring_auth': AWS_QUERYSTRING_AUTH,
            'file_overwrite': AWS_S3_FILE_OVERWRITE,
        },
    }

# WhiteNoise en producción
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# ==============================
# 🔐 LOGIN / LOGOUT
# ==============================
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/login/'


# ==============================
# 🔢 PRIMARY KEY
# ==============================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================
# 🔐 RECAPTCHA
# ==============================
RECAPTCHA_PUBLIC_KEY = os.environ.get(
    'RECAPTCHA_PUBLIC_KEY',
    '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI',
)

RECAPTCHA_PRIVATE_KEY = os.environ.get(
    'RECAPTCHA_PRIVATE_KEY',
    '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe',
)


# ==============================
# 🍽️ API EXTERNA (SPOONACULAR)
# ==============================
SPOONACULAR_API_KEY = os.environ.get('SPOONACULAR_API_KEY', '').strip()


# ==============================
# 📧 CONFIGURACIÓN DE EMAIL
# ==============================
# ⚠️ IMPORTANTE:
# En producción debes configurar estas variables en Render

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').strip().lower() in {'1', 'true', 'yes', 'on'}

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '').strip()
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '').strip()

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER).strip()


# ==============================
# 🔕 IGNORAR ERROR DE RECAPTCHA
# ==============================
SILENCED_SYSTEM_CHECKS = ['django_recaptcha.recaptcha_test_key_error']
