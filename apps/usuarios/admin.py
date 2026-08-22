from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import PerfilUsuario

Usuario = get_user_model()


class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    extra = 0
    max_num = 1
    can_delete = False


try:
    admin.site.unregister(Usuario)
except admin.sites.NotRegistered:
    pass


@admin.register(Usuario)
class UsuarioAdmin(DjangoUserAdmin):
    inlines = [PerfilUsuarioInline]


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "papel", "loja", "ativo", "deve_trocar_senha")
    list_filter = ("papel", "ativo", "deve_trocar_senha")
    search_fields = ("usuario__username", "usuario__first_name", "loja__codigo")
