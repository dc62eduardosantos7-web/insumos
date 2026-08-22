import decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("estoque", "0001_initial"), ("lojas", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Pedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("PENDENTE", "Pendente"), ("SEPARACAO", "Em separação"), ("FATURADO", "Faturado"), ("ENVIADO", "Enviado"), ("CONCLUIDO", "Concluído"), ("CANCELADO", "Cancelado")], default="PENDENTE", max_length=15)),
                ("observacoes", models.TextField(blank=True, verbose_name="observações")),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("loja", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pedidos", to="lojas.loja")),
            ],
            options={"verbose_name": "pedido", "verbose_name_plural": "pedidos", "ordering": ["-criado_em"]},
        ),
        migrations.CreateModel(
            name="ItemPedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantidade", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.01"))])),
                ("pedido", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="itens", to="pedidos.pedido")),
                ("produto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="itens_pedido", to="estoque.produto")),
            ],
            options={"verbose_name": "item do pedido", "verbose_name_plural": "itens do pedido"},
        ),
    ]
