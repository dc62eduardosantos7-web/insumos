from django.urls import path

from . import views

app_name = "estoque"

urlpatterns = [
    path("produtos/", views.produtos, name="produtos"),
    path("entradas/", views.entradas, name="entradas"),
    path("saidas/", views.saidas, name="saidas"),
    path("historico/", views.historico, name="historico"),
]
