import uuid

from django.db import models
from django.utils import timezone


class Romaneio(models.Model):
    STATUS = [
        ("GERADO", "Gerado na separação"),
        ("CANCELADO", "Cancelado"),
    ]

    numero = models.CharField("número", max_length=30, unique=True, blank=True)
    pedido = models.OneToOneField(
        "pedidos.Pedido", on_delete=models.PROTECT, related_name="romaneio"
    )
    transportadora = models.CharField(max_length=120, blank=True)
    placa = models.CharField(max_length=10, blank=True)
    motorista = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=STATUS, default="GERADO")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "romaneio"
        verbose_name_plural = "romaneios"

    def save(self, *args, **kwargs):
        if not self.numero:
            data = timezone.localdate().strftime("%Y%m%d")
            self.numero = f"ROM-{data}-{uuid.uuid4().hex[:6].upper()}"
        self.placa = self.placa.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero
