from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.usuarios.models import PerfilUsuario
from apps.usuarios.permissoes import obter_papel, obter_perfil

from . import services
from .forms import (
    ItensPedidoFormSet,
    JustificativaForm,
    ObservacaoForm,
    PedidoForm,
    QuantidadesPedidoForm,
)
from .models import ItemPedido, Pedido

PAPEIS_PEDIDOS = {
    PerfilUsuario.LOJA,
    PerfilUsuario.SUPPLY,
    PerfilUsuario.APROVADOR,
    PerfilUsuario.SEPARACAO,
    PerfilUsuario.ADMIN,
}


def _papel_valido(request):
    papel = obter_papel(request.user)
    if papel not in PAPEIS_PEDIDOS:
        raise PermissionDenied("Usuário sem perfil ativo no Controle de Insumos.")
    return papel


def _eh(papel, *permitidos):
    return papel == PerfilUsuario.ADMIN or papel in permitidos


def _pedidos_do_usuario(usuario):
    papel = obter_papel(usuario)
    queryset = (
        Pedido.objects.select_related(
            "loja", "criado_por", "conferido_por", "aprovado_por"
        )
        .prefetch_related("itens__produto")
        .all()
    )
    if papel == PerfilUsuario.LOJA:
        perfil = obter_perfil(usuario)
        return queryset.filter(loja=perfil.loja) if perfil and perfil.loja_id else queryset.none()
    if papel in PAPEIS_PEDIDOS:
        return queryset
    return queryset.none()


def _obter_pedido_visivel(request, pk):
    return get_object_or_404(_pedidos_do_usuario(request.user), pk=pk)


@login_required
def lista(request):
    papel = _papel_valido(request)
    pode_criar = _eh(papel, PerfilUsuario.LOJA, PerfilUsuario.SUPPLY)

    if request.method == "POST" and not pode_criar:
        raise PermissionDenied("Seu perfil não pode criar solicitações.")

    if request.method == "POST":
        form = PedidoForm(request.POST, usuario=request.user)
        itens_formset = ItensPedidoFormSet(request.POST, prefix="itens")
        if form.is_valid() and itens_formset.is_valid():
            if papel == PerfilUsuario.LOJA:
                perfil = obter_perfil(request.user)
                if not perfil or not perfil.loja_id:
                    raise PermissionDenied("Usuário sem loja vinculada.")
                loja = perfil.loja
            else:
                loja = form.cleaned_data["loja"]
            with transaction.atomic():
                pedido = Pedido.objects.create(
                    loja=loja,
                    lane=loja.lane,
                    data=form.cleaned_data["data"],
                    observacoes=form.cleaned_data["observacoes"],
                    status="ENVIADO_SUPPLY",
                    criado_por=request.user,
                )
                for item_form in itens_formset:
                    dados = item_form.cleaned_data
                    if not dados or not dados.get("produto"):
                        continue
                    ItemPedido.objects.create(
                        pedido=pedido,
                        produto=dados["produto"],
                        quantidade=dados["quantidade"],
                        observacao=dados["observacao"],
                    )
                services.registrar_historico(
                    pedido,
                    usuario=request.user,
                    acao="Solicitação criada e enviada ao Supply Chain",
                    status_anterior="RASCUNHO",
                    observacao=pedido.observacoes,
                )
            messages.success(
                request, f"Solicitação #{pedido.pk} enviada ao Supply Chain."
            )
            return redirect("pedidos:detalhe", pk=pedido.pk)
    else:
        form = PedidoForm(initial={"data": timezone.localdate()}, usuario=request.user)
        itens_formset = ItensPedidoFormSet(prefix="itens")

    status = request.GET.get("status", "")
    pedidos = _pedidos_do_usuario(request.user)
    status_validos = {codigo for codigo, _ in Pedido.STATUS}
    if status in status_validos:
        pedidos = pedidos.filter(status=status)
    return render(
        request,
        "pedidos/lista.html",
        {
            "form": form,
            "itens_formset": itens_formset,
            "pedidos": pedidos,
            "pode_criar": pode_criar,
            "status_filtro": status,
            "status_opcoes": Pedido.STATUS,
        },
    )


@login_required
def detalhe(request, pk):
    papel = _papel_valido(request)
    pedido = _obter_pedido_visivel(request, pk)
    itens = list(pedido.itens.select_related("produto"))
    contexto = {
        "pedido": pedido,
        "itens": itens,
        "historico": pedido.historico.select_related("usuario"),
        "ajuste_solicitado_form": QuantidadesPedidoForm(
            itens=itens, modo="solicitada"
        ),
        "ajuste_aprovado_form": QuantidadesPedidoForm(
            itens=itens, modo="aprovada"
        ),
        "separacao_form": QuantidadesPedidoForm(
            itens=itens, modo="separada", justificativa_obrigatoria=False
        ),
        "justificativa_form": JustificativaForm(),
        "observacao_form": ObservacaoForm(),
        "pode_iniciar_conferencia": _eh(papel, PerfilUsuario.SUPPLY)
        and pedido.status in {"ENVIADO_SUPPLY", "DEVOLVIDO_SUPPLY"},
        "pode_conferir": _eh(papel, PerfilUsuario.SUPPLY)
        and pedido.status == "EM_CONFERENCIA",
        "pode_corrigir_loja": _eh(papel, PerfilUsuario.LOJA)
        and pedido.status == "DEVOLVIDO_LOJA",
        "pode_aprovar": _eh(papel, PerfilUsuario.APROVADOR)
        and pedido.status == "AGUARDANDO_APROVACAO",
        "pode_iniciar_separacao": _eh(papel, PerfilUsuario.SEPARACAO)
        and pedido.status == "APROVADO",
        "pode_separar": _eh(papel, PerfilUsuario.SEPARACAO)
        and pedido.status == "EM_SEPARACAO",
        "pode_cancelar": papel == PerfilUsuario.ADMIN
        and not pedido.estoque_baixado_em
        and pedido.status != "CANCELADO",
        "pode_excluir": papel == PerfilUsuario.ADMIN
        and not pedido.estoque_baixado_em,
    }
    return render(request, "pedidos/detalhe.html", contexto)


def _validar_acao(papel, *permitidos):
    if not _eh(papel, *permitidos):
        raise PermissionDenied("Seu perfil não pode executar esta ação.")


def _erros_formulario(form):
    textos = []
    for erros in form.errors.values():
        textos.extend(str(erro) for erro in erros)
    return " ".join(textos) or "Confira os dados informados."


@require_POST
@login_required
def acao(request, pk, acao):
    papel = _papel_valido(request)
    pedido = _obter_pedido_visivel(request, pk)
    itens = list(pedido.itens.select_related("produto"))
    try:
        if acao == "iniciar-conferencia":
            _validar_acao(papel, PerfilUsuario.SUPPLY)
            services.iniciar_conferencia(pk, usuario=request.user)
            mensagem = "Conferência iniciada."
        elif acao == "ajustar-supply":
            _validar_acao(papel, PerfilUsuario.SUPPLY)
            form = QuantidadesPedidoForm(
                request.POST, itens=itens, modo="solicitada"
            )
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.ajustar_solicitacao(
                pk,
                usuario=request.user,
                quantidades=form.quantidades,
                justificativa=form.cleaned_data["justificativa"],
                acao="Quantidades ajustadas pelo Supply Chain",
            )
            mensagem = "Quantidades ajustadas e registradas."
        elif acao == "encaminhar-aprovacao":
            _validar_acao(papel, PerfilUsuario.SUPPLY)
            form = ObservacaoForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.encaminhar_aprovacao(
                pk,
                usuario=request.user,
                observacao=form.cleaned_data["observacao"],
            )
            mensagem = "Pedido enviado ao supervisor/gerente."
        elif acao == "devolver-loja":
            _validar_acao(papel, PerfilUsuario.SUPPLY)
            form = JustificativaForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.devolver(
                pk,
                usuario=request.user,
                destino="DEVOLVIDO_LOJA",
                justificativa=form.cleaned_data["justificativa"],
                origem_permitida={"EM_CONFERENCIA"},
            )
            mensagem = "Pedido devolvido para correção da loja."
        elif acao == "recusar-supply":
            _validar_acao(papel, PerfilUsuario.SUPPLY)
            form = JustificativaForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.recusar(
                pk,
                usuario=request.user,
                justificativa=form.cleaned_data["justificativa"],
                origem_permitida={"EM_CONFERENCIA"},
            )
            mensagem = "Solicitação recusada pelo Supply Chain."
        elif acao == "reenviar-loja":
            _validar_acao(papel, PerfilUsuario.LOJA)
            form = QuantidadesPedidoForm(
                request.POST, itens=itens, modo="solicitada"
            )
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.reenviar_loja(
                pk,
                usuario=request.user,
                quantidades=form.quantidades,
                justificativa=form.cleaned_data["justificativa"],
            )
            mensagem = "Solicitação corrigida e reenviada."
        elif acao == "aprovar":
            _validar_acao(papel, PerfilUsuario.APROVADOR)
            form = ObservacaoForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.aprovar(
                pk,
                usuario=request.user,
                justificativa=form.cleaned_data["observacao"],
            )
            mensagem = "Pedido aprovado e liberado para separação."
        elif acao == "ajustar-aprovar":
            _validar_acao(papel, PerfilUsuario.APROVADOR)
            form = QuantidadesPedidoForm(request.POST, itens=itens, modo="aprovada")
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.aprovar(
                pk,
                usuario=request.user,
                quantidades=form.quantidades,
                justificativa=form.cleaned_data["justificativa"],
            )
            mensagem = "Quantidades ajustadas e pedido aprovado."
        elif acao == "devolver-supply-aprovador":
            _validar_acao(papel, PerfilUsuario.APROVADOR)
            form = JustificativaForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.devolver(
                pk,
                usuario=request.user,
                destino="DEVOLVIDO_SUPPLY",
                justificativa=form.cleaned_data["justificativa"],
                origem_permitida={"AGUARDANDO_APROVACAO"},
            )
            mensagem = "Pedido devolvido ao Supply Chain."
        elif acao == "recusar-aprovador":
            _validar_acao(papel, PerfilUsuario.APROVADOR)
            form = JustificativaForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.recusar(
                pk,
                usuario=request.user,
                justificativa=form.cleaned_data["justificativa"],
                origem_permitida={"AGUARDANDO_APROVACAO"},
            )
            mensagem = "Solicitação recusada pelo supervisor/gerente."
        elif acao == "iniciar-separacao":
            _validar_acao(papel, PerfilUsuario.SEPARACAO)
            services.iniciar_separacao(pk, usuario=request.user)
            mensagem = "Separação iniciada."
        elif acao == "concluir-separacao":
            _validar_acao(papel, PerfilUsuario.SEPARACAO)
            form = QuantidadesPedidoForm(
                request.POST,
                itens=itens,
                modo="separada",
                justificativa_obrigatoria=False,
            )
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.concluir_separacao(
                pk,
                usuario=request.user,
                quantidades=form.quantidades,
                observacao=form.cleaned_data["justificativa"],
            )
            mensagem = "Separação concluída, estoque baixado e romaneio gerado."
        elif acao == "devolver-supply-separacao":
            _validar_acao(papel, PerfilUsuario.SEPARACAO)
            form = JustificativaForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.devolver(
                pk,
                usuario=request.user,
                destino="DEVOLVIDO_SUPPLY",
                justificativa=form.cleaned_data["justificativa"],
                origem_permitida={"APROVADO", "EM_SEPARACAO"},
            )
            mensagem = "Pedido devolvido ao Supply Chain por divergência."
        elif acao == "cancelar":
            if papel != PerfilUsuario.ADMIN:
                raise PermissionDenied("Somente administradores podem cancelar pedidos.")
            form = JustificativaForm(request.POST)
            if not form.is_valid():
                raise ValidationError(_erros_formulario(form))
            services.cancelar(
                pk,
                usuario=request.user,
                justificativa=form.cleaned_data["justificativa"],
            )
            mensagem = "Pedido cancelado."
        else:
            raise PermissionDenied("Ação desconhecida.")
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
    else:
        messages.success(request, mensagem)
    return redirect("pedidos:detalhe", pk=pedido.pk)


@login_required
def imprimir(request, pk):
    _papel_valido(request)
    pedido = _obter_pedido_visivel(request, pk)
    pedido = (
        Pedido.objects.select_related(
            "loja", "criado_por", "conferido_por", "aprovado_por", "separado_por"
        )
        .prefetch_related("itens__produto")
        .get(pk=pedido.pk)
    )
    return render(request, "pedidos/imprimir.html", {"pedido": pedido})


@require_POST
@login_required
@transaction.atomic
def excluir(request, pk):
    papel = _papel_valido(request)
    if papel != PerfilUsuario.ADMIN:
        raise PermissionDenied("Somente administradores podem excluir pedidos.")
    pedido = get_object_or_404(Pedido, pk=pk)
    if pedido.estoque_baixado_em:
        messages.error(request, "Pedidos com estoque baixado não podem ser excluídos.")
        return redirect("pedidos:detalhe", pk=pk)
    numero = pedido.pk
    romaneio = getattr(pedido, "romaneio", None)
    if romaneio is not None:
        romaneio.delete()
    pedido.delete()
    messages.success(request, f"Pedido #{numero} excluído com sucesso.")
    return redirect("pedidos:lista")
