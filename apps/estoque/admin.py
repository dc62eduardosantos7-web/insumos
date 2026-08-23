from django.contrib import admin

from config.admin_mixins import ExcluirTudoAdminMixin

from .models import ComposicaoKit, Movimentacao, Produto


class ComposicaoKitInline(admin.TabularInline):
    model = ComposicaoKit
    fk_name = "kit"
    extra = 0
    autocomplete_fields = ("item",)


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
        "tipo_produto",
        "categoria",
        "unidade",
        "saldo_disponivel",
        "estoque_minimo",
        "ativo",
    )
    list_filter = ("ativo", "unidade", "categoria")
    search_fields = ("codigo", "nome")
    readonly_fields = ("estoque_atual", "criado_em", "atualizado_em")
    inlines = [ComposicaoKitInline]

    @admin.display(description="tipo")
    def tipo_produto(self, obj):
        return "Kit" if obj.eh_kit else "Produto"

    @admin.display(description="saldo disponível")
    def saldo_disponivel(self, obj):
        return obj.estoque_disponivel

    def preparar_exclusao_total(self, request):
        ComposicaoKit.objects.all().delete()


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
