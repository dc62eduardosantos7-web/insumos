from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="deve_trocar_senha",
            field=models.BooleanField(
                default=False,
                help_text="Redireciona o usuário para cadastrar uma nova senha após entrar.",
                verbose_name="trocar senha no próximo acesso",
            ),
        ),
    ]
