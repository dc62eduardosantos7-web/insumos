from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.lojas.models import Loja
from apps.pedidos.models import ItemPedido, Pedido

from .models import ComposicaoKit, Movimentacao, Produto

Usuario = get_user_model()


class KitsPadraoTests(TestCase):
    def test_kit_novo_autozoner_contem_todos_os_itens(self):
        kit = Produto.objects.get(codigo="KIT-NOVO-AUTOZONER")

        self.assertEqual(
            set(kit.componentes_kit.values_list("item__nome", flat=True)),
            {
                "JACARÉ PARA CRACHÁ",
                "CRACHÁS",
                "PIN VIVA PROMESSA",
                "SACOCHILA",
                "COPO AUTOZONE",
                "CANETA",
                "CARTAO GRITO DE GUERRA",
                "FOLDER AUTOZONE",
                "CARTAO PROMESSA",
                "CARTAO SWILE",
            },
        )
        self.assertFalse(
            kit.componentes_kit.exclude(quantidade=Decimal("1")).exists()
        )

    def test_kit_operacao_contem_todos_os_itens(self):
        kit = Produto.objects.get(codigo="KIT-OPERACAO")

        self.assertEqual(
            set(kit.componentes_kit.values_list("item__nome", flat=True)),
            {
                "PIN VIVA PROMESSA",
                "SACOCHILA",
                "CANETA",
                "CARTAO GRITO DE GUERRA",
                "FOLDER AUTOZONE",
                "CARTAO PROMESSA",
                "GARRAFA PLASTICA",
                "CARTAO SWILE",
            },
        )
        self.assertFalse(
            kit.componentes_kit.exclude(quantidade=Decimal("1")).exists()
        )


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

    def test_excluir_tudo_apaga_produtos_e_preserva_usuarios(self):
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

    def test_excluir_tudo_apaga_historico_de_movimentacoes(self):
        Movimentacao.objects.create(
            tipo="E",
            produto=self.produto,
            quantidade=Decimal("5"),
            documento="TESTE-EXCLUSAO-HISTORICO",
            usuario=self.admin,
        )

        resposta = self.client.post(
            reverse("admin:estoque_produto_excluir_tudo"),
            {"confirmacao": "sim"},
        )

        self.assertRedirects(
            resposta, reverse("admin:estoque_produto_changelist")
        )
        self.assertFalse(Produto.objects.exists())
        self.assertFalse(Movimentacao.objects.exists())

    def test_produto_vinculado_a_pedido_cancela_exclusao(self):
        loja = Loja.objects.create(codigo="999", nome="Loja Proteção")
        pedido = Pedido.objects.create(loja=loja, criado_por=self.admin)
        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade=Decimal("1"),
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
        self.assertTrue(ItemPedido.objects.filter(pk=item.pk).exists())
