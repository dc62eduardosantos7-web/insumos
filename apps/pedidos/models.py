from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Pedido(models.Model):
    STATUS = [
        ("RASCUNHO", "Rascunho"),
        ("ENVIADO_SUPPLY", "Enviado ao Supply Chain"),
        ("EM_CONFERENCIA", "Em conferência pelo Supply Chain"),
        ("DEVOLVIDO_LOJA", "Devolvido para a loja"),
        ("AGUARDANDO_APROVACAO", "Aguardando aprovação"),
        ("DEVOLVIDO_SUPPLY", "Devolvido ao Supply Chain"),
        ("APROVADO", "Aprovado para separação"),
        ("RECUSADO", "Recusado"),
        ("EM_SEPARACAO", "Em separação"),
        ("PARCIAL", "Separado parcialmente"),
        ("SEPARADO", "Separado"),
        ("CANCELADO", "Cancelado"),
    ]

    loja = models.ForeignKey(
        "lojas.Loja", on_delete=models.PROTECT, related_name="pedidos"
    )
    romaneio = models.ForeignKey(
        "romaneio.Romaneio",
        on_delete=models.PROTECT,
        related_name="pedidos",
        null=True,
        blank=True,
    )
    lane = models.CharField(max_length=50, blank=True)
    data = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=25, choices=STATUS, default="ENVIADO_SUPPLY")
    observacoes = models.TextField("observações", blank=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_criados",
    )
    conferido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_conferidos",
    )
    conferido_em = models.DateTimeField(null=True, blank=True)
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_aprovados",
    )
    aprovado_em = models.DateTimeField(null=True, blank=True)
    separado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos_separados",
    )
    separado_em = models.DateTimeField(null=True, blank=True)
    estoque_baixado_em = models.DateTimeField(null=True, blank=True)
    motivo_ultima_acao = models.TextField("motivo da última ação", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self):
        return f"Pedido #{self.pk or 'novo'} - {self.loja}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(
        "estoque.Produto", on_delete=models.PROTECT, related_name="itens_pedido"
    )
    kit_origem = models.ForeignKey(
        "estoque.Produto",
        on_delete=models.PROTECT,
        related_name="itens_pedido_como_kit",
        null=True,
        blank=True,
    )
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    quantidade_aprovada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    quantidade_separada = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    observacao = models.CharField("observação", max_length=255, blank=True)

    class Meta:
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"

    def __str__(self):
        origem = f" ({self.kit_origem.nome})" if self.kit_origem_id else ""
        return f"{self.produto} × {self.quantidade}{origem}"

    @property
    def quantidade_liberada(self):
        return self.quantidade_aprovada or self.quantidade


class HistoricoPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="historico"
    )
    acao = models.CharField(max_length=80)
    status_anterior = models.CharField(max_length=25, blank=True)
    status_novo = models.CharField(max_length=25, blank=True)
    observacao = models.TextField("observação", blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acoes_em_pedidos",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "histórico do pedido"
        verbose_name_plural = "históricos dos pedidos"

    def __str__(self):
        return f"Pedido #{self.pedido_id} · {self.acao}"
