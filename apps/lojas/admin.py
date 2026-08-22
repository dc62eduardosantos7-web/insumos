from django.contrib import admin

from .models import Loja


@admin.register(Loja)
class LojaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "lane")
    search_fields = ("codigo", "nome", "lane")
