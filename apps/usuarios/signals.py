from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import PerfilUsuario


def _atualizar_privilegios(usuario, *, is_staff, is_superuser):
    campos = []
    if usuario.is_staff != is_staff:
        usuario.is_staff = is_staff
        campos.append("is_staff")
    if usuario.is_superuser != is_superuser:
        usuario.is_superuser = is_superuser
        campos.append("is_superuser")
    if campos:
        usuario.save(update_fields=campos)


@receiver(post_save, sender=PerfilUsuario)
def sincronizar_privilegios_admin(sender, instance, **kwargs):
    usuario = instance.usuario
    deve_ser_admin = instance.ativo and instance.papel == PerfilUsuario.ADMIN

    if deve_ser_admin:
        # Superusuários que já existiam são principais e não passam a ser
        # gerenciados pelo perfil do Controle de Insumos.
        gerenciado = instance.privilegios_admin_gerenciados
        if not usuario.is_superuser:
            gerenciado = True
        _atualizar_privilegios(usuario, is_staff=True, is_superuser=True)
        if gerenciado != instance.privilegios_admin_gerenciados:
            PerfilUsuario.objects.filter(pk=instance.pk).update(
                privilegios_admin_gerenciados=gerenciado
            )
            instance.privilegios_admin_gerenciados = gerenciado
    elif instance.privilegios_admin_gerenciados:
        _atualizar_privilegios(usuario, is_staff=False, is_superuser=False)
        PerfilUsuario.objects.filter(pk=instance.pk).update(
            privilegios_admin_gerenciados=False
        )
        instance.privilegios_admin_gerenciados = False


@receiver(post_delete, sender=PerfilUsuario)
def revogar_privilegios_ao_excluir_perfil(sender, instance, **kwargs):
    if instance.privilegios_admin_gerenciados:
        _atualizar_privilegios(
            instance.usuario,
            is_staff=False,
            is_superuser=False,
        )
