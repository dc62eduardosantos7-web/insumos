from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


COMPONENTES = {
    "JACARÉ PARA CRACHÁ": "KIT-COMP-001",
    "CRACHÁS": "KIT-COMP-002",
    "PIN VIVA PROMESSA": "KIT-COMP-003",
    "SACOCHILA": "KIT-COMP-004",
    "COPO AUTOZONE": "KIT-COMP-005",
    "CANETA": "KIT-COMP-006",
    "CARTAO GRITO DE GUERRA": "KIT-COMP-007",
    "FOLDER AUTOZONE": "KIT-COMP-008",
    "CARTAO PROMESSA": "KIT-COMP-009",
    "CARTAO SWILE": "KIT-COMP-010",
    "GARRAFA PLASTICA": "KIT-COMP-011",
}

KITS = {
    "KIT-NOVO-AUTOZONER": (
        "KIT NOVO AUTOZONER",
        [
            "JACARÉ PARA CRACHÁ",
            "CRACHÁS",
            "PIN VIVA PROMESSA",
            "SACOCHILA",
            "COPO AUTOZONE",
            "CANETA",
            "CARTAO GRITO DE GUERRA",
            "FOLDER AUTOZONE",
            "CARTAO PROMESSA",
            "CARTAO SWILE",
        ],
    ),
    "KIT-OPERACAO": (
        "KIT OPERAÇÃO",
        [
            "PIN VIVA PROMESSA",
            "SACOCHILA",
            "CANETA",
            "CARTAO GRITO DE GUERRA",
            "FOLDER AUTOZONE",
            "CARTAO PROMESSA",
            "GARRAFA PLASTICA",
            "CARTAO SWILE",
        ],
    ),
}


def configurar_kits(apps, schema_editor):
    Produto = apps.get_model("estoque", "Produto")
    ComposicaoKit = apps.get_model("estoque", "ComposicaoKit")

    produtos = {}
    for nome, codigo_reserva in COMPONENTES.items():
        produto = (
            Produto.objects.filter(nome__iexact=nome)
            .order_by("-estoque_atual", "pk")
            .first()
        )
        if produto is None:
            produto = Produto.objects.create(
                codigo=codigo_reserva,
                nome=nome,
                categoria="COMPONENTE DE KIT",
                unidade="UN",
                estoque_atual=Decimal("0"),
                estoque_minimo=Decimal("0"),
                ativo=True,
            )
        produtos[nome] = produto

    for codigo, (nome, componentes) in KITS.items():
        kit, _ = Produto.objects.get_or_create(
            codigo=codigo,
            defaults={
                "nome": nome,
                "categoria": "KIT",
                "unidade": "UN",
                "estoque_atual": Decimal("0"),
                "estoque_minimo": Decimal("0"),
                "ativo": True,
            },
        )
        campos_alterados = []
        for campo, valor in {
            "nome": nome,
            "categoria": "KIT",
            "unidade": "UN",
            "ativo": True,
        }.items():
            if getattr(kit, campo) != valor:
                setattr(kit, campo, valor)
                campos_alterados.append(campo)
        if campos_alterados:
            kit.save(update_fields=campos_alterados)

        ComposicaoKit.objects.filter(kit=kit).delete()
        ComposicaoKit.objects.bulk_create(
            [
                ComposicaoKit(
                    kit=kit,
                    item=produtos[nome_componente],
                    quantidade=Decimal("1"),
                )
                for nome_componente in componentes
            ]
        )


class Migration(migrations.Migration):
    dependencies = [("estoque", "0002_produto_observacao")]

    operations = [
        migrations.CreateModel(
            name="ComposicaoKit",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "quantidade",
                    models.DecimalField(
                        decimal_places=2,
                        default=1,
                        max_digits=12,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="componente_de_kits",
                        to="estoque.produto",
                    ),
                ),
                (
                    "kit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="componentes_kit",
                        to="estoque.produto",
                    ),
                ),
            ],
            options={
                "verbose_name": "componente do kit",
                "verbose_name_plural": "componentes do kit",
                "ordering": ["item__nome"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("kit", "item"),
                        name="componente_unico_por_kit",
                    )
                ],
            },
        ),
        migrations.RunPython(configurar_kits, migrations.RunPython.noop),
    ]
