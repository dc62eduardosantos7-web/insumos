from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import redirect, render

from apps.pedidos.models import Pedido
from apps.romaneio.models import Romaneio
from apps.usuarios.models import PerfilUsuario
from apps.usuarios.permissoes import obter_papel, obter_perfil, papeis_permitidos

from .forms import ImportacaoProdutosForm, MovimentacaoForm, ProdutoForm, SaidaForm
from .importers import importar_produtos_xlsx
from .models import Movimentacao, Produto
from .services import registrar_movimentacao


@papeis_permitidos(
    PerfilUsuario.LOJA,
    PerfilUsuario.SUPPLY,
    PerfilUsuario.APROVADOR,
    PerfilUsuario.SEPARACAO,
)
def dashboard(request):
    papel = obter_papel(request.user)
    pedidos = Pedido.objects.all()
    if papel == PerfilUsuario.LOJA:
        perfil = obter_perfil(request.user)
        pedidos = pedidos.filter(loja=perfil.loja) if perfil and perfil.loja_id else pedidos.none()
    produtos_baixos = Produto.objects.filter(
        ativo=True,
        componentes_kit__isnull=True,
        estoque_atual__lte=F("estoque_minimo"),
    )
    contexto = {
        "total_produtos": Produto.objects.filter(ativo=True).count(),
        "produtos_baixos": produtos_baixos[:8],
        "total_baixos": produtos_baixos.count(),
        "pedidos_abertos": pedidos.exclude(
            status__in=["PARCIAL", "SEPARADO", "RECUSADO", "CANCELADO"]
        ).count(),
        "romaneios_gerados": Romaneio.objects.filter(status="GERADO").count(),
        "movimentacoes": Movimentacao.objects.select_related("produto", "loja")[:8],
        "painel_loja": papel == PerfilUsuario.LOJA,
        "pedidos_aguardando": pedidos.filter(
            status__in=["ENVIADO_SUPPLY", "EM_CONFERENCIA", "AGUARDANDO_APROVACAO"]
        ).count(),
        "pedidos_em_separacao": pedidos.filter(
            status__in=["APROVADO", "EM_SEPARACAO"]
        ).count(),
        "pedidos_finalizados": pedidos.filter(
            status__in=["PARCIAL", "SEPARADO"]
        ).count(),
        "pedidos_recentes": pedidos.select_related("loja")[:8],
    }
    return render(request, "dashboard.html", contexto)


@papeis_permitidos(
    PerfilUsuario.SUPPLY,
    PerfilUsuario.SEPARACAO,
)
def produtos(request):
    pode_gerenciar = obter_papel(request.user) == PerfilUsuario.ADMIN
    if request.method == "POST" and not pode_gerenciar:
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("Somente administradores podem alterar produtos.")
    acao = request.POST.get("acao")
    form = ProdutoForm(request.POST or None) if acao != "importar" else ProdutoForm()
    importacao_form = (
        ImportacaoProdutosForm(request.POST, request.FILES)
        if acao == "importar"
        else ImportacaoProdutosForm()
    )
    if request.method == "POST" and acao == "cadastrar" and form.is_valid():
        form.save()
        messages.success(request, "Produto cadastrado com sucesso.")
        return redirect("estoque:produtos")
    if request.method == "POST" and acao == "importar" and importacao_form.is_valid():
        arquivo = importacao_form.cleaned_data["arquivo"]
        try:
            resultado = importar_produtos_xlsx(
                arquivo,
                usuario=request.user,
                nome_arquivo=arquivo.name,
            )
        except Exception as exc:
            importacao_form.add_error("arquivo", str(exc))
        else:
            messages.success(
                request,
                "Importação concluída: "
                f"{resultado['criados']} criados, "
                f"{resultado['atualizados']} atualizados, "
                f"{resultado['sem_alteracao']} sem alteração, "
                f"{resultado['descartados_menor_estoque']} repetidos com menor estoque descartados, "
                f"{len(resultado['erros'])} erros.",
            )
            return redirect("estoque:produtos")

    termo = request.GET.get("q", "").strip()
    lista = Produto.objects.filter(ativo=True).prefetch_related(
        "componentes_kit__item"
    )
    if termo:
        lista = lista.filter(Q(codigo__icontains=termo) | Q(nome__icontains=termo))
    return render(
        request,
        "estoque/produtos.html",
        {
            "form": form,
            "importacao_form": importacao_form,
            "produtos": lista,
            "termo": termo,
            "pode_gerenciar": pode_gerenciar,
        },
    )


@papeis_permitidos(PerfilUsuario.SEPARACAO)
def entradas(request):
    form = MovimentacaoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        registrar_movimentacao(
            tipo="E", usuario=request.user, **form.cleaned_data
        )
        messages.success(request, "Entrada registrada e saldo atualizado.")
        return redirect("estoque:entradas")
    return render(request, "estoque/entradas.html", {"form": form})


@papeis_permitidos(PerfilUsuario.SEPARACAO)
def saidas(request):
    form = SaidaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            registrar_movimentacao(
                tipo="S", usuario=request.user, **form.cleaned_data
            )
        except ValidationError as exc:
            form.add_error("quantidade", exc.messages[0])
        else:
            messages.success(request, "Saída registrada e saldo atualizado.")
            return redirect("estoque:saidas")
    return render(request, "estoque/saidas.html", {"form": form})


@papeis_permitidos(PerfilUsuario.SEPARACAO)
def historico(request):
    lista = Movimentacao.objects.select_related("produto", "loja", "usuario")
    tipo = request.GET.get("tipo", "")
    termo = request.GET.get("q", "").strip()
    if tipo in {"E", "S"}:
        lista = lista.filter(tipo=tipo)
    if termo:
        lista = lista.filter(
            Q(produto__codigo__icontains=termo)
            | Q(produto__nome__icontains=termo)
            | Q(produto_codigo__icontains=termo)
            | Q(produto_nome__icontains=termo)
            | Q(documento__icontains=termo)
        )
    pagina = Paginator(lista, 25).get_page(request.GET.get("page"))
    return render(
        request,
        "estoque/historico.html",
        {"pagina": pagina, "tipo": tipo, "termo": termo},
    )
