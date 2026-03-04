from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from clientes.forms import LoginUsuarioForm
from clientes.views import registro_usuario

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("carta.urls")),
    path("pedidos/", include("pedidos.urls")),
    path("clientes/", include("clientes.urls")),
    path('captcha/', include('captcha.urls')),
    path('registro/', registro_usuario, name='registro_publico'),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="login.html",
            authentication_form=LoginUsuarioForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


    
