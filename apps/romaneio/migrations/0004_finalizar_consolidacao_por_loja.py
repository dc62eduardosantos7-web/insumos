import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("pedidos", "0005_pedido_romaneio_consolidado"),
        ("romaneio", "0003_adicionar_loja"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="romaneio",
            name="pedido",
        ),
        migrations.AlterField(
            model_name="romaneio",
            name="loja",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="romaneio",
                to="lojas.loja",
            ),
        ),
    ]
