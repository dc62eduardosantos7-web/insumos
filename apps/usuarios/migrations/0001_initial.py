import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("lojas", "0002_loja_lane_simplificar"),
    ]

    operations = [
        migrations.CreateModel(
            name="PerfilUsuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("papel", models.CharField(choices=[("LOJA", "Loja"), ("SUPPLY", "Supply Chain"), ("APROVADOR", "Supervisor/Gerente aprovador"), ("SEPARACAO", "Equipe de separação"), ("EXPEDICAO", "Expedição"), ("ADMIN", "Administrador")], max_length=15)),
                ("ativo", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("loja", models.ForeignKey(blank=True, help_text="Obrigatório somente para usuários com o papel Loja.", null=True, on_delete=django.db.models.deletion.PROTECT, related_name="usuarios", to="lojas.loja")),
                ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="perfil_insumos", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "perfil de acesso", "verbose_name_plural": "perfis de acesso"},
        ),
    ]
