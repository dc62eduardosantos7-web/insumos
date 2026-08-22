from django.db import models


class Loja(models.Model):
    codigo = models.CharField("código", max_length=30, unique=True)
    nome = models.CharField(max_length=150)
    lane = models.CharField(max_length=50, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "loja"
        verbose_name_plural = "lojas"

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.strip().upper()
        self.lane = self.lane.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"
