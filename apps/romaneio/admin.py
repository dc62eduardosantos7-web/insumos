from django.contrib import admin

from config.admin_mixins import ExcluirTudoAdminMixin

from .models import Romaneio


@admin.register(Romaneio)
class RomaneioAdmin(ExcluirTudoAdminMixin, admin.ModelAdmin):
    excluir_tudo_descricao = (
        "Os pedidos serão preservados e apenas deixarão de estar vinculados a um "
        "romaneio. Lojas, produtos, estoque e usuários não serão alterados."
    )
    list_display = (
        "numero",
        "loja",
        "total_pedidos",
        "transportadora",
        "placa",
        "motorista",
        "status",
        "criado_em",
    )
    list_filter = ("status", "criado_em")
    search_fields = ("numero", "loja__codigo", "loja__nome", "placa", "motorista")
    readonly_fields = ("numero", "criado_em")

    @admin.display(description="pedidos")
    def total_pedidos(self, obj):
        return obj.pedidos.count()

    def preparar_exclusao_total(self, request):
        from apps.pedidos.models import Pedido

        Pedido.objects.filter(romaneio__isnull=False).update(romaneio=None)
