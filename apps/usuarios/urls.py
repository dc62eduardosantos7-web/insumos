from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("importar-logins/", views.importar_logins, name="importar_logins"),
    path("trocar-senha/", views.TrocarSenhaView.as_view(), name="trocar_senha"),
]
