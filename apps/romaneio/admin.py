from django.contrib import admin

from .models import Romaneio


@admin.register(Romaneio)
class RomaneioAdmin(admin.ModelAdmin):
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
