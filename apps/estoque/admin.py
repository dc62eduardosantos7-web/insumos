from django.contrib import admin
from django.db.models import Q

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
        "Somente os produtos comuns serão apagados. KIT NOVO AUTOZONER, "
        "KIT OPERAÇÃO e todos os componentes necessários para esses kits serão "
        "preservados e reativados. Histórico, pedidos, romaneios, lojas e usuários "
        "não serão apagados. Produtos usados em pedidos antigos ficarão arquivados."
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

    def get_queryset(self, request):
        return super().get_queryset(request).filter(ativo=True)

    def get_excluir_tudo_queryset(self, request):
        preservados = set(
            Produto.objects.filter(
                codigo__in=("KIT-NOVO-AUTOZONER", "KIT-OPERACAO")
            ).values_list("pk", flat=True)
        )
        preservados.update(
            ComposicaoKit.objects.filter(kit_id__in=preservados).values_list(
                "item_id", flat=True
            )
        )
        return Produto.objects.exclude(pk__in=preservados)

    def executar_exclusao_total(self, request):
        alvos = self.get_excluir_tudo_queryset(request)
        vinculados = alvos.filter(
            Q(itens_pedido__isnull=False)
            | Q(itens_pedido_como_kit__isnull=False)
        ).distinct()
        ids_vinculados = list(vinculados.values_list("pk", flat=True))
        total_arquivados = vinculados.update(ativo=False)
        deletaveis = alvos.exclude(pk__in=ids_vinculados)
        total_excluidos = deletaveis.count()
        deletaveis.delete()

        kits = Produto.objects.filter(
            codigo__in=("KIT-NOVO-AUTOZONER", "KIT-OPERACAO")
        )
        ids_preservados = set(kits.values_list("pk", flat=True))
        ids_preservados.update(
            ComposicaoKit.objects.filter(kit_id__in=ids_preservados).values_list(
                "item_id", flat=True
            )
        )
        Produto.objects.filter(pk__in=ids_preservados).update(ativo=True)
        return (
            f"{total_excluidos} produto(s) comum(ns) foram excluídos e "
            f"{total_arquivados} permaneceram arquivados por estarem em pedidos. "
            "Os kits, seus componentes e o histórico foram preservados."
        )


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = (
        "criado_em",
        "tipo",
        "produto_historico",
        "quantidade",
        "loja",
        "usuario",
    )
    list_filter = ("tipo", "criado_em")
    search_fields = (
        "produto__codigo",
        "produto__nome",
        "produto_codigo",
        "produto_nome",
        "documento",
    )
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

    @admin.display(description="produto")
    def produto_historico(self, obj):
        return f"{obj.codigo_produto} - {obj.nome_produto}"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
