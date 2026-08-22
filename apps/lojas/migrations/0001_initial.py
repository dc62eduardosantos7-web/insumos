from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Loja",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(max_length=30, unique=True, verbose_name="código")),
                ("nome", models.CharField(max_length=150)),
                ("endereco", models.CharField(blank=True, max_length=255, verbose_name="endereço")),
                ("cidade", models.CharField(blank=True, max_length=100)),
                ("uf", models.CharField(blank=True, max_length=2, verbose_name="UF")),
                ("ativo", models.BooleanField(default=True, verbose_name="ativa")),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "loja", "verbose_name_plural": "lojas", "ordering": ["codigo"]},
        )
    ]
