from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse


class ExcluirTudoAdminMixin:
    """Adiciona uma exclusão total protegida ao changelist do Django Admin."""

    change_list_template = "admin/excluir_tudo_change_list.html"
    excluir_tudo_descricao = ""

    def get_urls(self):
        opts = self.model._meta
        urls = [
            path(
                "excluir-tudo/",
                self.admin_site.admin_view(self.excluir_tudo_view),
                name=f"{opts.app_label}_{opts.model_name}_excluir_tudo",
            )
        ]
        return urls + super().get_urls()

    def get_excluir_tudo_url(self):
        opts = self.model._meta
        return reverse(
            f"admin:{opts.app_label}_{opts.model_name}_excluir_tudo"
        )

    def get_changelist_url(self):
        opts = self.model._meta
        return reverse(
            f"admin:{opts.app_label}_{opts.model_name}_changelist"
        )

    def pode_excluir_tudo(self, request):
        return request.user.is_superuser and self.has_delete_permission(request)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(
            {
                "pode_excluir_tudo": self.pode_excluir_tudo(request),
                "excluir_tudo_url": self.get_excluir_tudo_url(),
            }
        )
        return super().changelist_view(request, extra_context=extra_context)

    def preparar_exclusao_total(self, request):
        """Ponto de extensão para remover vínculos antes da exclusão."""

    def excluir_tudo_view(self, request):
        if not self.pode_excluir_tudo(request):
            raise PermissionDenied

        queryset = self.model._default_manager.all()
        total = queryset.count()

        if request.method == "POST":
            if request.POST.get("confirmacao") != "sim":
                self.message_user(
                    request,
                    "Marque a confirmação antes de excluir os registros.",
                    level=messages.ERROR,
                )
            else:
                with transaction.atomic():
                    total = self.model._default_manager.count()
                    self.preparar_exclusao_total(request)
                    self.model._default_manager.all().delete()

                self.message_user(
                    request,
                    f"{total} registro(s) de {self.model._meta.verbose_name_plural} "
                    "foram excluídos.",
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(self.get_changelist_url())

        context = {
            **self.admin_site.each_context(request),
            "title": f"Excluir todos os {self.model._meta.verbose_name_plural}",
            "opts": self.model._meta,
            "total": total,
            "descricao": self.excluir_tudo_descricao,
            "voltar_url": self.get_changelist_url(),
        }
        return TemplateResponse(
            request,
            "admin/excluir_tudo_confirmation.html",
            context,
        )
