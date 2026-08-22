from django.db import migrations, models


def converter_perfis_expedicao(apps, schema_editor):
    PerfilUsuario = apps.get_model("usuarios", "PerfilUsuario")
    PerfilUsuario.objects.filter(papel="EXPEDICAO").update(papel="SEPARACAO")


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0002_perfilusuario_deve_trocar_senha"),
    ]

    operations = [
        migrations.RunPython(converter_perfis_expedicao, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="perfilusuario",
            name="papel",
            field=models.CharField(
                choices=[
                    ("LOJA", "Loja"),
                    ("SUPPLY", "Supply Chain"),
                    ("APROVADOR", "Supervisor/Gerente aprovador"),
                    ("SEPARACAO", "Equipe de separação"),
                    ("ADMIN", "Administrador"),
                ],
                max_length=15,
            ),
        ),
    ]
