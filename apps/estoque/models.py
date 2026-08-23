from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Produto(models.Model):
    UNIDADES = [
        ("UN", "Unidade"),
        ("CX", "Caixa"),
        ("KG", "Quilograma"),
        ("LT", "Litro"),
        ("PCT", "Pacote"),
    ]

    codigo = models.CharField("código", max_length=30, unique=True)
    nome = models.CharField(max_length=150)
    categoria = models.CharField(max_length=100, blank=True)
    observacao = models.TextField("observação", blank=True)
    unidade = models.CharField(max_length=3, choices=UNIDADES, default="UN")
    estoque_atual = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, editable=False
    )
    estoque_minimo = models.DecimalField(
        "estoque mínimo",
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal("0"))],
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "produto"
        verbose_name_plural = "produtos"

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.strip().upper()
        super().save(*args, **kwargs)

    @property
    def abaixo_do_minimo(self):
        return self.estoque_disponivel <= self.estoque_minimo

    @property
    def eh_kit(self):
        return self.componentes_kit.exists()

    @property
    def estoque_disponivel(self):
        componentes = list(self.componentes_kit.all())
        if not componentes:
            return self.estoque_atual
        return min(
            componente.item.estoque_atual // componente.quantidade
            for componente in componentes
        )

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class ComposicaoKit(models.Model):
    kit = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
        related_name="componentes_kit",
    )
    item = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="componente_de_kits",
    )
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        ordering = ["item__nome"]
        verbose_name = "componente do kit"
        verbose_name_plural = "componentes do kit"
        constraints = [
            models.UniqueConstraint(
                fields=["kit", "item"],
                name="componente_unico_por_kit",
            )
        ]

    def clean(self):
        if self.kit_id and self.item_id and self.kit_id == self.item_id:
            raise ValidationError("Um kit não pode conter a si próprio.")

    def __str__(self):
        return f"{self.kit.nome}: {self.quantidade} × {self.item.nome}"


class Movimentacao(models.Model):
    TIPOS = [("E", "Entrada"), ("S", "Saída")]

    tipo = models.CharField(max_length=1, choices=TIPOS)
    produto = models.ForeignKey(
        Produto, on_delete=models.PROTECT, related_name="movimentacoes"
    )
    loja = models.ForeignKey(
        "lojas.Loja",
        on_delete=models.PROTECT,
        related_name="movimentacoes",
        null=True,
        blank=True,
    )
    quantidade = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    documento = models.CharField(max_length=80, blank=True)
    observacao = models.TextField("observação", blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimentacoes_estoque",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "movimentação"
        verbose_name_plural = "movimentações"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantidade__gt=0),
                name="movimentacao_quantidade_positiva",
            )
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.produto} - {self.quantidade}"
