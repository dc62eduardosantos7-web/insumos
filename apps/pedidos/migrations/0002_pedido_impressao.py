import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("pedidos", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="data",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
        migrations.AddField(
            model_name="pedido",
            name="lane",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="itempedido",
            name="observacao",
            field=models.CharField(blank=True, max_length=255, verbose_name="observação"),
        ),
    ]
