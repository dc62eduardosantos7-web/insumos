from django.contrib import admin

from config.admin_mixins import ExcluirTudoAdminMixin

from .models import Movimentacao, Produto


@admin.register(Produto)
class ProdutoAdmin(ExcluirTudoAdminMixin, admin.ModelAdmin):
    excluir_tudo_descricao = (
        "Todos os produtos serão removidos, mas lojas, usuários, pedidos, "
        "romaneios e estoque histórico serão preservados. Se houver produto "
        "vinculado a um pedido ou movimentação, a operação inteira será cancelada."
    )
    list_display = (
        "codigo",
        "nome",
        "categoria",
        "unidade",
        "estoque_atual",
        "estoque_minimo",
        "ativo",
    )
    list_filter = ("ativo", "unidade", "categoria")
    search_fields = ("codigo", "nome")
    readonly_fields = ("estoque_atual", "criado_em", "atualizado_em")


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "tipo", "produto", "quantidade", "loja", "usuario")
    list_filter = ("tipo", "criado_em")
    search_fields = ("produto__codigo", "produto__nome", "documento")
    readonly_fields = (
        "tipo",
        "produto",
        "quantidade",
        "loja",
        "documento",
        "observacao",
        "usuario",
        "criado_em",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
