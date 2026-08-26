from django.db import migrations, models


def sincronizar_administradores_existentes(apps, schema_editor):
    PerfilUsuario = apps.get_model("usuarios", "PerfilUsuario")
    for perfil in PerfilUsuario.objects.filter(papel="ADMIN", ativo=True).select_related(
        "usuario"
    ):
        usuario = perfil.usuario
        # Preserva como principal qualquer superusuário que já existia antes
        # desta automação.
        gerenciado = not usuario.is_superuser
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.save(update_fields=["is_staff", "is_superuser"])
        if gerenciado:
            perfil.privilegios_admin_gerenciados = True
            perfil.save(update_fields=["privilegios_admin_gerenciados"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("usuarios", "0003_remover_perfil_expedicao")]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="privilegios_admin_gerenciados",
            field=models.BooleanField(
                default=False,
                editable=False,
                help_text=(
                    "Indica que is_staff/is_superuser foram concedidos "
                    "automaticamente pelo papel Administrador."
                ),
            ),
        ),
        migrations.RunPython(sincronizar_administradores_existentes, noop),
    ]
