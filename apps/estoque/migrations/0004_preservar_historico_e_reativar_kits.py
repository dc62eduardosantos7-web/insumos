from django.db import migrations, models
import django.db.models.deletion


CODIGOS_KITS = ("KIT-NOVO-AUTOZONER", "KIT-OPERACAO")


def preservar_historico_e_reativar_kits(apps, schema_editor):
    Produto = apps.get_model("estoque", "Produto")
    Movimentacao = apps.get_model("estoque", "Movimentacao")
    ComposicaoKit = apps.get_model("estoque", "ComposicaoKit")

    for movimentacao in Movimentacao.objects.select_related("produto").iterator():
        if movimentacao.produto_id:
            movimentacao.produto_codigo = movimentacao.produto.codigo
            movimentacao.produto_nome = movimentacao.produto.nome
            movimentacao.produto_unidade = movimentacao.produto.unidade
            movimentacao.save(
                update_fields=(
                    "produto_codigo",
                    "produto_nome",
                    "produto_unidade",
                )
            )

    ids_kits = set(
        Produto.objects.filter(codigo__in=CODIGOS_KITS).values_list(
            "pk", flat=True
        )
    )
    ids_preservados = set(ids_kits)
    ids_preservados.update(
        ComposicaoKit.objects.filter(kit_id__in=ids_kits).values_list(
            "item_id", flat=True
        )
    )
    Produto.objects.filter(pk__in=ids_preservados).update(ativo=True)


class Migration(migrations.Migration):
    dependencies = [("estoque", "0003_composicaokit_e_kits_padrao")]

    operations = [
        migrations.AddField(
            model_name="movimentacao",
            name="produto_codigo",
            field=models.CharField(blank=True, editable=False, max_length=30),
        ),
        migrations.AddField(
            model_name="movimentacao",
            name="produto_nome",
            field=models.CharField(blank=True, editable=False, max_length=150),
        ),
        migrations.AddField(
            model_name="movimentacao",
            name="produto_unidade",
            field=models.CharField(blank=True, editable=False, max_length=3),
        ),
        migrations.AlterField(
            model_name="movimentacao",
            name="produto",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="movimentacoes",
                to="estoque.produto",
            ),
        ),
        migrations.RunPython(
            preservar_historico_e_reativar_kits,
            migrations.RunPython.noop,
        ),
    ]
