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

    def test_excluir_tudo_remove_comuns_e_preserva_kits(self):
        segundo_produto = Produto.objects.create(
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
        self.assertFalse(Produto.objects.filter(pk=self.produto.pk).exists())
        self.assertFalse(Produto.objects.filter(pk=segundo_produto.pk).exists())
        kits = Produto.objects.filter(
            codigo__in=("KIT-NOVO-AUTOZONER", "KIT-OPERACAO"),
            ativo=True,
        )
        self.assertEqual(kits.count(), 2)
        self.assertEqual(ComposicaoKit.objects.count(), 18)
        self.assertFalse(
            Produto.objects.filter(componente_de_kits__isnull=False).exclude(
                ativo=True
            ).exists()
        )
        self.assertTrue(Usuario.objects.filter(pk=self.admin.pk).exists())

    def test_excluir_tudo_preserva_historico_sem_produto(self):
        movimentacao = Movimentacao.objects.create(
            tipo="E",
            produto=self.produto,
            quantidade=Decimal("5"),
            documento="TESTE-PRESERVAR-HISTORICO",
            usuario=self.admin,
        )

        resposta = self.client.post(
            reverse("admin:estoque_produto_excluir_tudo"),
            {"confirmacao": "sim"},
        )

        self.assertRedirects(
            resposta, reverse("admin:estoque_produto_changelist")
        )
        self.assertFalse(Produto.objects.filter(pk=self.produto.pk).exists())
        movimentacao.refresh_from_db()
        self.assertIsNone(movimentacao.produto_id)
        self.assertEqual(movimentacao.produto_codigo, "PROD-001")
        self.assertEqual(movimentacao.produto_nome, "Produto para exclusão")

    def test_produto_vinculado_a_pedido_permanece_arquivado(self):
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

        self.assertRedirects(
            resposta, reverse("admin:estoque_produto_changelist")
        )
        self.produto.refresh_from_db()
        self.assertFalse(self.produto.ativo)
        self.assertTrue(ItemPedido.objects.filter(pk=item.pk).exists())
