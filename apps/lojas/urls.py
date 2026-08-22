from django.urls import path

from . import views

app_name = "lojas"

urlpatterns = [path("", views.lista, name="lista")]
