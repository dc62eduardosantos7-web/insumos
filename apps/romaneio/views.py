from decimal import Decimal

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.usuarios.models import PerfilUsuario
from apps.usuarios.permissoes import obter_papel, papeis_permitidos

from .models import Romaneio


@papeis_permitidos(PerfilUsuario.SEPARACAO)
def lista(request):
    romaneios = Romaneio.objects.select_related("loja").prefetch_related("pedidos")
    return render(
        request,
        "romaneio/lista.html",
        {
            "romaneios": romaneios,
            "pode_excluir": obter_papel(request.user) == PerfilUsuario.ADMIN,
        },
    )


def _itens_consolidados(romaneio):
    itens = {}
    for pedido in romaneio.pedidos.all():
        for item in pedido.itens.all():
            if item.quantidade_separada <= 0:
                continue
            chave = item.produto_id
            consolidado = itens.setdefault(
                chave,
                {
                    "codigo": item.produto.codigo,
                    "nome": item.produto.nome,
                    "unidade": item.produto.unidade,
                    "solicitado": Decimal("0"),
                    "aprovado": Decimal("0"),
                    "separado": Decimal("0"),
                    "pedidos": [],
                    "observacoes": [],
                },
            )
            consolidado["solicitado"] += item.quantidade
            consolidado["aprovado"] += (
                item.quantidade_aprovada
                if item.quantidade_aprovada is not None
                else item.quantidade
            )
            consolidado["separado"] += item.quantidade_separada
            if pedido.pk not in consolidado["pedidos"]:
                consolidado["pedidos"].append(pedido.pk)
            if item.observacao and item.observacao not in consolidado["observacoes"]:
                consolidado["observacoes"].append(item.observacao)
            if item.kit_origem_id:
                origem = f"Componente de {item.kit_origem.nome}"
                if origem not in consolidado["observacoes"]:
                    consolidado["observacoes"].append(origem)
    return sorted(itens.values(), key=lambda item: (item["nome"], item["codigo"]))


@papeis_permitidos(PerfilUsuario.SEPARACAO)
def imprimir(request, pk):
    romaneio = get_object_or_404(
        Romaneio.objects.select_related("loja").prefetch_related(
            "pedidos__itens__produto",
            "pedidos__itens__kit_origem",
            "pedidos__separado_por",
        ),
        pk=pk,
    )
    pedidos = list(romaneio.pedidos.all())
    return render(
        request,
        "romaneio/imprimir.html",
        {
            "romaneio": romaneio,
            "pedidos": pedidos,
            "itens": _itens_consolidados(romaneio),
        },
    )


@require_POST
@papeis_permitidos(PerfilUsuario.ADMIN)
def excluir(request, pk):
    romaneio = get_object_or_404(
        Romaneio.objects.select_related("loja").prefetch_related("pedidos"), pk=pk
    )
    numero = romaneio.numero
    if romaneio.pedidos.filter(estoque_baixado_em__isnull=False).exists():
        messages.error(
            request,
            "Romaneios com pedidos já separados não podem ser excluídos.",
        )
        return redirect("romaneio:lista")
    romaneio.delete()
    messages.success(request, f"Romaneio {numero} excluído com sucesso.")
    return redirect("romaneio:lista")
