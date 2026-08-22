from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import PerfilUsuario


def obter_perfil(usuario):
    if not getattr(usuario, "is_authenticated", False):
        return None
    try:
        perfil = usuario.perfil_insumos
    except PerfilUsuario.DoesNotExist:
        return None
    return perfil if perfil.ativo else None


def obter_papel(usuario):
    if not getattr(usuario, "is_authenticated", False):
        return None
    if usuario.is_superuser or usuario.is_staff:
        return PerfilUsuario.ADMIN
    perfil = obter_perfil(usuario)
    return perfil.papel if perfil else None


def tem_papel(usuario, *papeis):
    papel = obter_papel(usuario)
    return papel == PerfilUsuario.ADMIN or papel in papeis


def papeis_permitidos(*papeis):
    def decorator(view):
        @login_required
        @wraps(view)
        def protegida(request, *args, **kwargs):
            if tem_papel(request.user, *papeis):
                return view(request, *args, **kwargs)
            messages.error(request, "Seu perfil não tem permissão para esta ação.")
            return redirect("dashboard")

        return protegida

    return decorator
