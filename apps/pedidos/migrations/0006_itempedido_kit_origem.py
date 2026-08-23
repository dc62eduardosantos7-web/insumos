from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("estoque", "0003_composicaokit_e_kits_padrao"),
        ("pedidos", "0005_pedido_romaneio_consolidado"),
    ]

    operations = [
        migrations.AddField(
            model_name="itempedido",
            name="kit_origem",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="itens_pedido_como_kit",
                to="estoque.produto",
            ),
        )
    ]
