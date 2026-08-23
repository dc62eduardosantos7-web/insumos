from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Movimentacao, Produto

Usuario = get_user_model()


class AdminProdutoExcluirTudoTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            username="admin-produtos",
            email="admin-produtos@example.com",
            password="teste123",
        )
        self.client.force_login(self.admin)
        self.produto = Produto.objects.create(
            codigo="PROD-001",
            nome="Produto para exclusão",
            estoque_atual=Decimal("10"),
            unidade="UN",
        )

    def test_admin_exibe_botao_excluir_tudo_em_produtos(self):
        resposta = self.client.get(reverse("admin:estoque_produto_changelist"))

        self.assertContains(resposta, "Excluir tudo")

    def test_excluir_todos_produtos_sem_vinculos(self):
        Produto.objects.create(
            codigo="PROD-002",
            nome="Segundo produto",
            unidade="CX",
        )

        resposta = self.client.post(
            reverse("admin:estoque_produto_excluir_tudo"),
            {"confirmacao": "sim"},
        )

        self.assertRedirects(
            resposta, reverse("admin:estoque_produto_changelist")
        )
        self.assertFalse(Produto.objects.exists())
        self.assertTrue(Usuario.objects.filter(pk=self.admin.pk).exists())

    def test_produto_vinculado_cancela_exclusao_sem_apagar_dados(self):
        movimentacao = Movimentacao.objects.create(
            tipo="E",
            produto=self.produto,
            quantidade=Decimal("5"),
            documento="TESTE-PROTECAO",
            usuario=self.admin,
        )

        resposta = self.client.post(
            reverse("admin:estoque_produto_excluir_tudo"),
            {"confirmacao": "sim"},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta,
            "A exclusão foi cancelada porque existem registros vinculados.",
        )
        self.assertTrue(Produto.objects.filter(pk=self.produto.pk).exists())
        self.assertTrue(Movimentacao.objects.filter(pk=movimentacao.pk).exists())
