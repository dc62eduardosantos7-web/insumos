from .models import PerfilUsuario
from .permissoes import obter_papel, obter_perfil


def perfil_usuario(request):
    perfil = obter_perfil(request.user)
    papel = obter_papel(request.user)
    return {
        "perfil_usuario": perfil,
        "papel_usuario": papel,
        "PAPEL_LOJA": PerfilUsuario.LOJA,
        "PAPEL_SUPPLY": PerfilUsuario.SUPPLY,
        "PAPEL_APROVADOR": PerfilUsuario.APROVADOR,
        "PAPEL_SEPARACAO": PerfilUsuario.SEPARACAO,
        "PAPEL_ADMIN": PerfilUsuario.ADMIN,
    }
