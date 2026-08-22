from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve

from .permissoes import obter_perfil


class TrocaSenhaObrigatoriaMiddleware:
    ROTAS_PERMITIDAS = {"usuarios:trocar_senha", "logout"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, "user", None)
        if usuario and usuario.is_authenticated and not usuario.is_staff:
            perfil = obter_perfil(usuario)
            if perfil and perfil.deve_trocar_senha:
                caminho = request.path_info
                if not caminho.startswith((settings.STATIC_URL, settings.MEDIA_URL)):
                    rota = resolve(caminho).view_name
                    if rota not in self.ROTAS_PERMITIDAS:
                        return redirect("usuarios:trocar_senha")
        return self.get_response(request)
