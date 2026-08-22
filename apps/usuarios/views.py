from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import ImportacaoLoginsLojasForm
from .importers import importar_logins_lojas
from .models import PerfilUsuario
from .permissoes import obter_perfil, papeis_permitidos


@papeis_permitidos(PerfilUsuario.ADMIN)
def importar_logins(request):
    form = ImportacaoLoginsLojasForm(request.POST or None, request.FILES or None)
    resultado = None
    if request.method == "POST" and form.is_valid():
        try:
            resultado = importar_logins_lojas(
                form.cleaned_data["arquivo"],
                form.cleaned_data["redefinir_senhas"],
            )
        except ValueError as exc:
            form.add_error("arquivo", str(exc))
        else:
            total = resultado.usuarios_criados + resultado.usuarios_existentes
            if resultado.erros:
                messages.warning(
                    request,
                    f"Importação concluída com {total} usuário(s) processado(s) e "
                    f"{len(resultado.erros)} linha(s) com erro.",
                )
            else:
                messages.success(
                    request,
                    f"Importação concluída: {resultado.usuarios_criados} usuário(s) "
                    f"criado(s) e {resultado.usuarios_existentes} já existente(s).",
                )
            form = ImportacaoLoginsLojasForm()
    return render(
        request,
        "usuarios/importar_logins.html",
        {"form": form, "resultado": resultado},
    )


class TrocarSenhaView(LoginRequiredMixin, PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        perfil = obter_perfil(self.request.user)
        if perfil and perfil.deve_trocar_senha:
            perfil.deve_trocar_senha = False
            perfil.save(update_fields=["deve_trocar_senha", "atualizado_em"])
        messages.success(self.request, "Senha alterada com sucesso.")
        return super().form_valid(form)
