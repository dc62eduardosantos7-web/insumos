import django.db.models.deletion
from django.db import migrations, models


def preencher_loja(apps, schema_editor):
    Romaneio = apps.get_model("romaneio", "Romaneio")
    banco = schema_editor.connection.alias
    for romaneio in Romaneio.objects.using(banco).select_related("pedido"):
        if romaneio.pedido_id:
            romaneio.loja_id = romaneio.pedido.loja_id
            romaneio.save(using=banco, update_fields=["loja"])


class Migration(migrations.Migration):
    dependencies = [
        ("lojas", "0002_loja_lane_simplificar"),
        ("pedidos", "0004_remover_etapa_expedicao"),
        ("romaneio", "0002_romaneio_status_gerado"),
    ]

    operations = [
        migrations.AlterField(
            model_name="romaneio",
            name="pedido",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="romaneio_legado",
                to="pedidos.pedido",
            ),
        ),
        migrations.AddField(
            model_name="romaneio",
            name="loja",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="romaneio",
                to="lojas.loja",
            ),
        ),
        migrations.RunPython(preencher_loja, migrations.RunPython.noop),
    ]
