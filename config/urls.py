from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.estoque.views import dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("django.contrib.auth.urls")),
    path("usuarios/", include("apps.usuarios.urls")),
    path("", dashboard, name="dashboard"),
    path("estoque/", include("apps.estoque.urls")),
    path("lojas/", include("apps.lojas.urls")),
    path("pedidos/", include("apps.pedidos.urls")),
    path("romaneios/", include("apps.romaneio.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Controle de Insumos"
admin.site.site_title = "Administração"
admin.site.index_title = "Painel administrativo"
