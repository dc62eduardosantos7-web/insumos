import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


def migrar_pedidos_antigos(apps, schema_editor):
    Pedido = apps.get_model("pedidos", "Pedido")
    ItemPedido = apps.get_model("pedidos", "ItemPedido")
    mapa = {
        "PENDENTE": "ENVIADO_SUPPLY",
        "SEPARACAO": "EM_SEPARACAO",
        "FATURADO": "SEPARADO",
        "ENVIADO": "EXPEDIDO",
        "CONCLUIDO": "ENTREGUE",
    }
    for antigo, novo in mapa.items():
        Pedido.objects.filter(status=antigo).update(status=novo)

    pedidos_liberados = Pedido.objects.filter(
        status__in=["EM_SEPARACAO", "SEPARADO", "EXPEDIDO", "ENTREGUE"]
    ).values_list("pk", flat=True)
    ItemPedido.objects.filter(pedido_id__in=pedidos_liberados).update(
        quantidade_aprovada=models.F("quantidade")
    )
    pedidos_atendidos = Pedido.objects.filter(
        status__in=["SEPARADO", "EXPEDIDO", "ENTREGUE"]
    ).values_list("pk", flat=True)
    ItemPedido.objects.filter(pedido_id__in=pedidos_atendidos).update(
        quantidade_separada=models.F("quantidade")
    )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pedidos", "0002_pedido_impressao"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pedido",
            name="status",
            field=models.CharField(choices=[("RASCUNHO", "Rascunho"), ("ENVIADO_SUPPLY", "Enviado ao Supply Chain"), ("EM_CONFERENCIA", "Em conferência pelo Supply Chain"), ("DEVOLVIDO_LOJA", "Devolvido para a loja"), ("AGUARDANDO_APROVACAO", "Aguardando aprovação"), ("DEVOLVIDO_SUPPLY", "Devolvido ao Supply Chain"), ("APROVADO", "Aprovado para separação"), ("RECUSADO", "Recusado"), ("EM_SEPARACAO", "Em separação"), ("PARCIAL", "Separado parcialmente"), ("SEPARADO", "Separado"), ("EXPEDIDO", "Expedido"), ("ENTREGUE", "Entregue"), ("CANCELADO", "Cancelado")], default="ENVIADO_SUPPLY", max_length=25),
        ),
        migrations.AddField(model_name="pedido", name="aprovado_em", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="pedido", name="conferido_em", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="pedido", name="entregue_em", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="pedido", name="estoque_baixado_em", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="pedido", name="expedido_em", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="pedido", name="motivo_ultima_acao", field=models.TextField(blank=True, verbose_name="motivo da última ação")),
        migrations.AddField(model_name="pedido", name="separado_em", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="pedido", name="aprovado_por", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pedidos_aprovados", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="pedido", name="conferido_por", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pedidos_conferidos", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="pedido", name="criado_por", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pedidos_criados", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="pedido", name="expedido_por", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pedidos_expedidos", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="pedido", name="separado_por", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="pedidos_separados", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="itempedido", name="quantidade_aprovada", field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
        migrations.AddField(model_name="itempedido", name="quantidade_separada", field=models.DecimalField(decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0"))])),
        migrations.CreateModel(
            name="HistoricoPedido",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("acao", models.CharField(max_length=80)),
                ("status_anterior", models.CharField(blank=True, max_length=25)),
                ("status_novo", models.CharField(blank=True, max_length=25)),
                ("observacao", models.TextField(blank=True, verbose_name="observação")),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("pedido", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="historico", to="pedidos.pedido")),
                ("usuario", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="acoes_em_pedidos", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "histórico do pedido", "verbose_name_plural": "históricos dos pedidos", "ordering": ["-criado_em"]},
        ),
        migrations.RunPython(migrar_pedidos_antigos, migrations.RunPython.noop),
    ]
