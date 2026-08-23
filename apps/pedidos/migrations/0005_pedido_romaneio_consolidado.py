import django.db.models.deletion
from django.db import migrations, models


def consolidar_romaneios_por_loja(apps, schema_editor):
    Pedido = apps.get_model("pedidos", "Pedido")
    Romaneio = apps.get_model("romaneio", "Romaneio")
    banco = schema_editor.connection.alias
    principais = {}

    romaneios = Romaneio.objects.using(banco).order_by("loja_id", "criado_em", "pk")
    for romaneio in romaneios:
        if not romaneio.loja_id or not romaneio.pedido_id:
            continue

        principal = principais.get(romaneio.loja_id)
        if principal is None:
            principal = romaneio
            principais[romaneio.loja_id] = principal
        else:
            campos_atualizados = []
            for campo in ("transportadora", "placa", "motorista"):
                if not getattr(principal, campo) and getattr(romaneio, campo):
                    setattr(principal, campo, getattr(romaneio, campo))
                    campos_atualizados.append(campo)
            if principal.status != "GERADO" and romaneio.status == "GERADO":
                principal.status = "GERADO"
                campos_atualizados.append("status")
            if campos_atualizados:
                principal.save(using=banco, update_fields=campos_atualizados)

        Pedido.objects.using(banco).filter(pk=romaneio.pedido_id).update(
            romaneio_id=principal.pk
        )
        if romaneio.pk != principal.pk:
            romaneio.delete(using=banco)


def restaurar_pedido_principal(apps, schema_editor):
    Pedido = apps.get_model("pedidos", "Pedido")
    Romaneio = apps.get_model("romaneio", "Romaneio")
    banco = schema_editor.connection.alias
    for romaneio in Romaneio.objects.using(banco).all():
        pedido = (
            Pedido.objects.using(banco)
            .filter(romaneio_id=romaneio.pk)
            .order_by("pk")
            .first()
        )
        if pedido:
            romaneio.pedido_id = pedido.pk
            romaneio.save(using=banco, update_fields=["pedido"])
    Pedido.objects.using(banco).update(romaneio=None)


class Migration(migrations.Migration):
    dependencies = [
        ("pedidos", "0004_remover_etapa_expedicao"),
        ("romaneio", "0003_adicionar_loja"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="romaneio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="pedidos",
                to="romaneio.romaneio",
            ),
        ),
        migrations.RunPython(
            consolidar_romaneios_por_loja,
            restaurar_pedido_principal,
        ),
    ]
