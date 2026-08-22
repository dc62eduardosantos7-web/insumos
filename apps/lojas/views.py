from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect, render

from apps.usuarios.models import PerfilUsuario
from apps.usuarios.permissoes import papeis_permitidos

from .forms import ImportacaoLojasForm, LojaForm
from .importers import importar_cronograma_pdf
from .models import Loja


@papeis_permitidos(PerfilUsuario.ADMIN)
def lista(request):
    acao = request.POST.get("acao")
    form = LojaForm(request.POST or None) if acao != "importar" else LojaForm()
    importacao_form = (
        ImportacaoLojasForm(request.POST, request.FILES)
        if acao == "importar"
        else ImportacaoLojasForm()
    )
    if request.method == "POST" and acao == "cadastrar" and form.is_valid():
        form.save()
        messages.success(request, "Loja cadastrada com sucesso.")
        return redirect("lojas:lista")
    if request.method == "POST" and acao == "importar" and importacao_form.is_valid():
        arquivo = importacao_form.cleaned_data["arquivo"]
        try:
            resultado = importar_cronograma_pdf(arquivo)
        except Exception as exc:
            importacao_form.add_error("arquivo", str(exc))
        else:
            messages.success(
                request,
                "Cronograma importado: "
                f"{resultado['criados']} criadas, "
                f"{resultado['atualizados']} atualizadas, "
                f"{resultado['sem_alteracao']} sem alteração, "
                f"{resultado['lojas']} lojas e "
                f"{resultado['ocorrencias']} registros lidos.",
            )
            if resultado["multiplas_lanes"]:
                messages.info(
                    request,
                    f"{resultado['multiplas_lanes']} lojas aparecem em mais de "
                    "uma lane; todas foram preservadas no cadastro.",
                )
            for divergencia in resultado["divergencias"][:5]:
                messages.error(request, divergencia)
            return redirect("lojas:lista")

    termo = request.GET.get("q", "").strip()
    lojas = Loja.objects.all()
    if termo:
        lojas = lojas.filter(
            Q(codigo__icontains=termo)
            | Q(nome__icontains=termo)
            | Q(lane__icontains=termo)
        )
    return render(
        request,
        "lojas/lista.html",
        {
            "form": form,
            "importacao_form": importacao_form,
            "lojas": lojas,
            "termo": termo,
        },
    )
