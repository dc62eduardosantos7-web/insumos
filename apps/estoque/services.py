from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Movimentacao, Produto


@transaction.atomic
def registrar_movimentacao(
    *, produto, tipo, quantidade, loja=None, documento="", observacao="", usuario=None
):
    quantidade = Decimal(quantidade)
    if quantidade <= 0:
        raise ValidationError("A quantidade deve ser maior que zero.")

    produto_bloqueado = Produto.objects.select_for_update().get(pk=produto.pk)
    if tipo == "S" and produto_bloqueado.estoque_atual < quantidade:
        raise ValidationError(
            f"Estoque insuficiente. Saldo disponível: "
            f"{produto_bloqueado.estoque_atual} {produto_bloqueado.unidade}."
        )

    variacao = quantidade if tipo == "E" else -quantidade
    produto_bloqueado.estoque_atual += variacao
    produto_bloqueado.save(update_fields=["estoque_atual", "atualizado_em"])

    return Movimentacao.objects.create(
        tipo=tipo,
        produto=produto_bloqueado,
        quantidade=quantidade,
        loja=loja,
        documento=documento,
        observacao=observacao,
        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
    )
