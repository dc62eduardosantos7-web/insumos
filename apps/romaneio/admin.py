from django.contrib import admin

from .models import Romaneio


@admin.register(Romaneio)
class RomaneioAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "pedido",
        "transportadora",
        "placa",
        "motorista",
        "status",
        "criado_em",
    )
    list_filter = ("status", "criado_em")
    search_fields = ("numero", "pedido__loja__codigo", "placa", "motorista")
    readonly_fields = ("numero", "criado_em")
