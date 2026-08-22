from django.db import migrations, models


def converter_pedidos_finalizados(apps, schema_editor):
    Pedido = apps.get_model("pedidos", "Pedido")
    for pedido in Pedido.objects.filter(status__in=["EXPEDIDO", "ENTREGUE"]):
        itens = list(pedido.itens.all())
        atendimento_total = bool(itens) and all(
            item.quantidade_separada
            == (item.quantidade_aprovada or item.quantidade)
            for item in itens
        )
        pedido.status = "SEPARADO" if atendimento_total else "PARCIAL"
        pedido.save(update_fields=["status"])


class Migration(migrations.Migration):
    dependencies = [
        ("pedidos", "0003_fluxo_aprovacao"),
    ]

    operations = [
        migrations.RunPython(converter_pedidos_finalizados, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="pedido",
            name="status",
            field=models.CharField(
                choices=[
                    ("RASCUNHO", "Rascunho"),
                    ("ENVIADO_SUPPLY", "Enviado ao Supply Chain"),
                    ("EM_CONFERENCIA", "Em conferência pelo Supply Chain"),
                    ("DEVOLVIDO_LOJA", "Devolvido para a loja"),
                    ("AGUARDANDO_APROVACAO", "Aguardando aprovação"),
                    ("DEVOLVIDO_SUPPLY", "Devolvido ao Supply Chain"),
                    ("APROVADO", "Aprovado para separação"),
                    ("RECUSADO", "Recusado"),
                    ("EM_SEPARACAO", "Em separação"),
                    ("PARCIAL", "Separado parcialmente"),
                    ("SEPARADO", "Separado"),
                    ("CANCELADO", "Cancelado"),
                ],
                default="ENVIADO_SUPPLY",
                max_length=25,
            ),
        ),
        migrations.RemoveField(
            model_name="pedido",
            name="entregue_em",
        ),
        migrations.RemoveField(
            model_name="pedido",
            name="expedido_em",
        ),
        migrations.RemoveField(
            model_name="pedido",
            name="expedido_por",
        ),
    ]
