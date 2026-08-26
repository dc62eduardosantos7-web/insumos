from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class PerfilUsuario(models.Model):
    LOJA = "LOJA"
    SUPPLY = "SUPPLY"
    APROVADOR = "APROVADOR"
    SEPARACAO = "SEPARACAO"
    ADMIN = "ADMIN"

    PAPEIS = [
        (LOJA, "Loja"),
        (SUPPLY, "Supply Chain"),
        (APROVADOR, "Supervisor/Gerente aprovador"),
        (SEPARACAO, "Equipe de separação"),
        (ADMIN, "Administrador"),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_insumos",
    )
    papel = models.CharField(max_length=15, choices=PAPEIS)
    loja = models.ForeignKey(
        "lojas.Loja",
        on_delete=models.PROTECT,
        related_name="usuarios",
        null=True,
        blank=True,
        help_text="Obrigatório somente para usuários com o papel Loja.",
    )
    ativo = models.BooleanField(default=True)
    deve_trocar_senha = models.BooleanField(
        "trocar senha no próximo acesso",
        default=False,
        help_text="Redireciona o usuário para cadastrar uma nova senha após entrar.",
    )
    privilegios_admin_gerenciados = models.BooleanField(
        default=False,
        editable=False,
        help_text=(
            "Indica que is_staff/is_superuser foram concedidos automaticamente "
            "pelo papel Administrador."
        ),
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil de acesso"
        verbose_name_plural = "perfis de acesso"

    def clean(self):
        super().clean()
        if self.papel == self.LOJA and not self.loja_id:
            raise ValidationError({"loja": "Selecione a loja vinculada ao usuário."})
        if self.papel != self.LOJA:
            self.loja = None

    def __str__(self):
        return f"{self.usuario.username} · {self.get_papel_display()}"
