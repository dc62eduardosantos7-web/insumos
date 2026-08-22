import decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("lojas", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Produto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(max_length=30, unique=True, verbose_name="código")),
                ("nome", models.CharField(max_length=150)),
                ("categoria", models.CharField(blank=True, max_length=100)),
                ("unidade", models.CharField(choices=[("UN", "Unidade"), ("CX", "Caixa"), ("KG", "Quilograma"), ("LT", "Litro"), ("PCT", "Pacote")], default="UN", max_length=3)),
                ("estoque_atual", models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=12)),
                ("estoque_minimo", models.DecimalField(decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0"))], verbose_name="estoque mínimo")),
                ("ativo", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "produto", "verbose_name_plural": "produtos", "ordering": ["nome"]},
        ),
        migrations.CreateModel(
            name="Movimentacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=[("E", "Entrada"), ("S", "Saída")], max_length=1)),
                ("quantidade", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.01"))])),
                ("documento", models.CharField(blank=True, max_length=80)),
                ("observacao", models.TextField(blank=True, verbose_name="observação")),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("loja", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="movimentacoes", to="lojas.loja")),
                ("produto", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="movimentacoes", to="estoque.produto")),
                ("usuario", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="movimentacoes_estoque", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "movimentação", "verbose_name_plural": "movimentações", "ordering": ["-criado_em"]},
        ),
        migrations.AddConstraint(
            model_name="movimentacao",
            constraint=models.CheckConstraint(condition=models.Q(("quantidade__gt", 0)), name="movimentacao_quantidade_positiva"),
        ),
    ]
