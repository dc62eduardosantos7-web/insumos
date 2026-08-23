from django.urls import path

from . import views

app_name = "romaneio"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<int:pk>/imprimir/", views.imprimir, name="imprimir"),
    path("<int:pk>/excluir/", views.excluir, name="excluir"),
]
