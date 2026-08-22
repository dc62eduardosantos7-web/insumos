from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<int:pk>/", views.detalhe, name="detalhe"),
    path("<int:pk>/acao/<slug:acao>/", views.acao, name="acao"),
    path("<int:pk>/imprimir/", views.imprimir, name="imprimir"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
]
