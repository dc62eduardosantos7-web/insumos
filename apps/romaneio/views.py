from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.usuarios.models import PerfilUsuario
from apps.usuarios.permissoes import obter_papel, papeis_permitidos

from .models import Romaneio


@papeis_permitidos(PerfilUsuario.SEPARACAO)
def lista(request):
    romaneios = Romaneio.objects.select_related("pedido__loja")
    return render(
        request,
        "romaneio/lista.html",
        {
            "romaneios": romaneios,
            "pode_excluir": obter_papel(request.user) == PerfilUsuario.ADMIN,
        },
    )


@require_POST
@papeis_permitidos(PerfilUsuario.ADMIN)
def excluir(request, pk):
    romaneio = get_object_or_404(Romaneio.objects.select_related("pedido"), pk=pk)
    numero = romaneio.numero
    pedido = romaneio.pedido
    if pedido.estoque_baixado_em:
        messages.error(
            request,
            "Romaneios de pedidos com separação concluída não podem ser excluídos.",
        )
        return redirect("romaneio:lista")
    romaneio.delete()
    messages.success(request, f"Romaneio {numero} excluído com sucesso.")
    return redirect("romaneio:lista")
