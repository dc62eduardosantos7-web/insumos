from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.estoque.services import registrar_movimentacao
from apps.romaneio.models import Romaneio

from .models import HistoricoPedido, Pedido


def _usuario_ou_none(usuario):
    return usuario if getattr(usuario, "is_authenticated", False) else None


def registrar_historico(
    pedido, *, usuario, acao, status_anterior="", observacao=""
):
    return HistoricoPedido.objects.create(
        pedido=pedido,
        usuario=_usuario_ou_none(usuario),
        acao=acao,
        status_anterior=status_anterior,
        status_novo=pedido.status,
        observacao=observacao,
    )


def _carregar(pedido_id):
    return (
        Pedido.objects.select_for_update()
        .select_related("loja")
        .prefetch_related("itens__produto")
        .get(pk=pedido_id)
    )


def _validar_status(pedido, permitidos):
    if pedido.status not in permitidos:
        raise ValidationError(
            f"A ação não é permitida quando o pedido está como "
            f"{pedido.get_status_display()}."
        )


def _mudar_status(pedido, novo_status, *, usuario, acao, observacao="", campos=None):
    anterior = pedido.status
    pedido.status = novo_status
    pedido.motivo_ultima_acao = observacao
    atualizar = ["status", "motivo_ultima_acao", "atualizado_em"]
    if campos:
        for nome, valor in campos.items():
            setattr(pedido, nome, valor)
            atualizar.append(nome)
    pedido.save(update_fields=atualizar)
    registrar_historico(
        pedido,
        usuario=usuario,
        acao=acao,
        status_anterior=anterior,
        observacao=observacao,
    )
    return pedido


@transaction.atomic
def iniciar_conferencia(pedido_id, *, usuario):
    pedido = _carregar(pedido_id)
    _validar_status(pedido, {"ENVIADO_SUPPLY", "DEVOLVIDO_SUPPLY"})
    return _mudar_status(
        pedido,
        "EM_CONFERENCIA",
        usuario=usuario,
        acao="Conferência iniciada pelo Supply Chain",
    )


@transaction.atomic
def ajustar_solicitacao(pedido_id, *, usuario, quantidades, justificativa, acao):
    pedido = _carregar(pedido_id)
    _validar_status(pedido, {"EM_CONFERENCIA", "DEVOLVIDO_LOJA"})
    alteracoes = []
    for item in pedido.itens.all():
        nova = quantidades[item.pk]
        if nova <= 0:
            raise ValidationError("As quantidades solicitadas devem ser positivas.")
        if item.quantidade != nova:
            alteracoes.append(f"{item.produto.codigo}: {item.quantidade} → {nova}")
            item.quantidade = nova
            item.quantidade_aprovada = None
            item.quantidade_separada = 0
            item.save(
                update_fields=[
                    "quantidade",
                    "quantidade_aprovada",
                    "quantidade_separada",
                ]
            )
    if not alteracoes:
        alteracoes.append("Nenhuma quantidade foi modificada")
    observacao = f"{justificativa}. " + "; ".join(alteracoes)
    registrar_historico(
        pedido,
        usuario=usuario,
        acao=acao,
        status_anterior=pedido.status,
        observacao=observacao,
    )
    pedido.motivo_ultima_acao = justificativa
    pedido.save(update_fields=["motivo_ultima_acao", "atualizado_em"])
    return pedido


@transaction.atomic
def reenviar_loja(pedido_id, *, usuario, quantidades, justificativa):
    pedido = ajustar_solicitacao(
        pedido_id,
        usuario=usuario,
        quantidades=quantidades,
        justificativa=justificativa,
        acao="Solicitação corrigida pela loja",
    )
    return _mudar_status(
        pedido,
        "ENVIADO_SUPPLY",
        usuario=usuario,
        acao="Solicitação reenviada ao Supply Chain",
        observacao=justificativa,
    )


@transaction.atomic
def encaminhar_aprovacao(pedido_id, *, usuario, observacao=""):
    pedido = _carregar(pedido_id)
    _validar_status(pedido, {"EM_CONFERENCIA"})
    agora = timezone.now()
    return _mudar_status(
        pedido,
        "AGUARDANDO_APROVACAO",
        usuario=usuario,
        acao="Conferido e encaminhado para aprovação",
        observacao=observacao,
        campos={"conferido_por": usuario, "conferido_em": agora},
    )


@transaction.atomic
def devolver(pedido_id, *, usuario, destino, justificativa, origem_permitida):
    pedido = _carregar(pedido_id)
    _validar_status(pedido, set(origem_permitida))
    descricao = "loja" if destino == "DEVOLVIDO_LOJA" else "Supply Chain"
    return _mudar_status(
        pedido,
        destino,
        usuario=usuario,
        acao=f"Pedido devolvido para {descricao}",
        observacao=justificativa,
    )


@transaction.atomic
def recusar(pedido_id, *, usuario, justificativa, origem_permitida):
    pedido = _carregar(pedido_id)
    _validar_status(pedido, set(origem_permitida))
    return _mudar_status(
        pedido,
        "RECUSADO",
        usuario=usuario,
        acao="Solicitação recusada",
        observacao=justificativa,
    )


@transaction.atomic
def aprovar(pedido_id, *, usuario, quantidades=None, justificativa=""):
    pedido = _carregar(pedido_id)
    _validar_status(pedido, {"AGUARDANDO_APROVACAO"})
    alteracoes = []
    for item in pedido.itens.all():
        nova = quantidades[item.pk] if quantidades else item.quantidade
        if nova <= 0:
            raise ValidationError("As quantidades aprovadas devem ser positivas.")
        if nova != item.quantidade:
            alteracoes.append(f"{item.produto.codigo}: {item.quantidade} → {nova}")
        item.quantidade_aprovada = nova
        item.quantidade_separada = 0
        item.save(update_fields=["quantidade_aprovada", "quantidade_separada"])
    if alteracoes:
        justificativa = f"{justificativa}. " + "; ".join(alteracoes)
    agora = timezone.now()
    return _mudar_status(
        pedido,
        "APROVADO",
        usuario=usuario,
        acao="Pedido aprovado para separação",
        observacao=justificativa,
        campos={"aprovado_por": usuario, "aprovado_em": agora},
    )


@transaction.atomic
def iniciar_separacao(pedido_id, *, usuario):
    pedido = _carregar(pedido_id)
    _validar_status(pedido, {"APROVADO"})
    return _mudar_status(
        pedido,
        "EM_SEPARACAO",
        usuario=usuario,
        acao="Separação iniciada",
    )


@transaction.atomic
def concluir_separacao(pedido_id, *, usuario, quantidades, observacao=""):
    pedido = _carregar(pedido_id)
    _validar_status(pedido, {"EM_SEPARACAO", "APROVADO"})
    total_separado = 0
    atendimento_total = True
    detalhes = []
    for item in pedido.itens.all():
        liberada = item.quantidade_liberada
        separada = quantidades[item.pk]
        if separada < 0 or separada > liberada:
            raise ValidationError(
                f"{item.produto.nome}: informe entre 0 e {liberada}."
            )
        if separada > item.produto.estoque_atual:
            raise ValidationError(
                f"{item.produto.nome}: estoque disponível de "
                f"{item.produto.estoque_atual} {item.produto.unidade}."
            )
        item.quantidade_separada = separada
        item.save(update_fields=["quantidade_separada"])
        total_separado += separada
        atendimento_total = atendimento_total and separada == liberada
        detalhes.append(f"{item.produto.codigo}: {separada}/{liberada}")
    if total_separado <= 0:
        raise ValidationError("Informe ao menos um item separado.")

    for item in pedido.itens.all():
        if item.quantidade_separada <= 0:
            continue
        registrar_movimentacao(
            produto=item.produto,
            tipo="S",
            quantidade=item.quantidade_separada,
            loja=pedido.loja,
            documento=f"PEDIDO-{pedido.pk}",
            observacao=f"Baixa automática ao concluir a separação do pedido #{pedido.pk}",
            usuario=usuario,
        )

    novo_status = "SEPARADO" if atendimento_total else "PARCIAL"
    texto = "; ".join(detalhes)
    if observacao:
        texto = f"{observacao}. {texto}"
    agora = timezone.now()
    romaneio, _ = Romaneio.objects.select_for_update().get_or_create(
        loja=pedido.loja,
        defaults={"status": "GERADO"},
    )
    if romaneio.status != "GERADO":
        romaneio.status = "GERADO"
        romaneio.save(update_fields=["status"])
    return _mudar_status(
        pedido,
        novo_status,
        usuario=usuario,
        acao=(
            f"Separação concluída · Romaneio {romaneio.numero}"
            if atendimento_total
            else f"Separação parcial concluída · Romaneio {romaneio.numero}"
        ),
        observacao=texto,
        campos={
            "romaneio": romaneio,
            "separado_por": usuario,
            "separado_em": agora,
            "estoque_baixado_em": agora,
        },
    )


@transaction.atomic
def cancelar(pedido_id, *, usuario, justificativa):
    pedido = _carregar(pedido_id)
    if pedido.estoque_baixado_em:
        raise ValidationError(
            "Pedidos com separação concluída não podem ser cancelados sem estorno de estoque."
        )
    romaneio = pedido.romaneio if pedido.romaneio_id else None
    if romaneio and not romaneio.pedidos.exclude(pk=pedido.pk).exists():
        romaneio.status = "CANCELADO"
        romaneio.save(update_fields=["status"])
    return _mudar_status(
        pedido,
        "CANCELADO",
        usuario=usuario,
        acao="Pedido cancelado",
        observacao=justificativa,
        campos={"romaneio": None} if romaneio else None,
    )
