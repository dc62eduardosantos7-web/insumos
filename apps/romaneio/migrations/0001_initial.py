import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("pedidos", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Romaneio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("numero", models.CharField(blank=True, max_length=30, unique=True, verbose_name="número")),
                ("transportadora", models.CharField(blank=True, max_length=120)),
                ("placa", models.CharField(blank=True, max_length=10)),
                ("motorista", models.CharField(blank=True, max_length=120)),
                ("status", models.CharField(choices=[("ABERTO", "Aberto"), ("EXPEDIDO", "Expedido"), ("ENTREGUE", "Entregue"), ("CANCELADO", "Cancelado")], default="ABERTO", max_length=12)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("pedido", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="romaneio", to="pedidos.pedido")),
            ],
            options={"verbose_name": "romaneio", "verbose_name_plural": "romaneios", "ordering": ["-criado_em"]},
        )
    ]
