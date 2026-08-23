from django.contrib import admin

from config.admin_mixins import ExcluirTudoAdminMixin

from .models import HistoricoPedido, ItemPedido, Pedido


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 1


class HistoricoPedidoInline(admin.TabularInline):
    model = HistoricoPedido
    extra = 0
    can_delete = False
    readonly_fields = (
        "acao",
        "status_anterior",
        "status_novo",
        "observacao",
        "usuario",
        "criado_em",
    )


@admin.register(Pedido)
class PedidoAdmin(ExcluirTudoAdminMixin, admin.ModelAdmin):
    excluir_tudo_descricao = (
        "Os itens e históricos vinculados aos pedidos também serão removidos. "
        "Produtos, lojas, estoque, usuários e romaneios não serão excluídos."
    )
    list_display = (
        "id",
        "loja",
        "lane",
        "data",
        "status",
        "criado_por",
        "criado_em",
    )
    list_filter = ("status", "criado_em")
    search_fields = ("=id", "loja__codigo", "loja__nome")
    inlines = [ItemPedidoInline, HistoricoPedidoInline]
