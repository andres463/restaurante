from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import OportunidadRuleta, Perfil


@receiver(post_save, sender=User)
def crear_perfil(sender, instance, created, **kwargs):
    if created and not (instance.is_staff or instance.is_superuser):
        perfil = Perfil.objects.create(usuario=instance)
        OportunidadRuleta.objects.get_or_create(
            perfil=perfil,
            accion='registro',
        )


@receiver(post_save, sender=User)
def guardar_perfil(sender, instance, **kwargs):
    if hasattr(instance, 'perfil'):
        instance.perfil.save()
