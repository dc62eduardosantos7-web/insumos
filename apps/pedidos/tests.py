from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.estoque.models import Movimentacao, Produto
from apps.lojas.models import Loja
from apps.romaneio.models import Romaneio
from apps.usuarios.models import PerfilUsuario

from .models import Pedido

Usuario = get_user_model()


class FluxoPedidoTests(TestCase):
    def setUp(self):
        self.loja = Loja.objects.create(codigo="001", nome="Loja Um", lane="01")
        self.outra_loja = Loja.objects.create(
            codigo="002", nome="Loja Dois", lane="02"
        )
        self.produto = Produto.objects.create(
            codigo="INS-001",
            nome="Bobina",
            estoque_atual=Decimal("100"),
            unidade="CX",
        )
        self.usuario_loja = self.criar_usuario(
            "loja001", PerfilUsuario.LOJA, self.loja
        )
        self.usuario_outra_loja = self.criar_usuario(
            "loja002", PerfilUsuario.LOJA, self.outra_loja
        )
        self.supply = self.criar_usuario("supply", PerfilUsuario.SUPPLY)
        self.aprovador = self.criar_usuario(
            "aprovador", PerfilUsuario.APROVADOR
        )
        self.separacao = self.criar_usuario(
            "separacao", PerfilUsuario.SEPARACAO
        )

    def criar_usuario(self, username, papel, loja=None):
        usuario = Usuario.objects.create_user(username=username, password="teste123")
        PerfilUsuario.objects.create(usuario=usuario, papel=papel, loja=loja)
        return usuario

    def criar_solicitacao(self, quantidade="10"):
        self.client.force_login(self.usuario_loja)
        resposta = self.client.post(
            reverse("pedidos:lista"),
            {
                "data": "2026-08-22",
                "observacoes": "Pedido de teste",
                "itens-TOTAL_FORMS": "1",
                "itens-INITIAL_FORMS": "0",
                "itens-MIN_NUM_FORMS": "0",
                "itens-MAX_NUM_FORMS": "1000",
                "itens-0-produto": str(self.produto.pk),
                "itens-0-quantidade": quantidade,
                "itens-0-observacao": "Urgente",
            },
        )
        self.assertEqual(resposta.status_code, 302)
        return Pedido.objects.latest("pk")

    def executar_acao(self, usuario, pedido, acao, dados=None):
        self.client.force_login(usuario)
        return self.client.post(
            reverse("pedidos:acao", args=[pedido.pk, acao]), dados or {}
        )

    def test_loja_cria_e_enxerga_apenas_os_proprios_pedidos(self):
        pedido = self.criar_solicitacao()
        self.assertEqual(pedido.loja, self.loja)
        self.assertEqual(pedido.status, "ENVIADO_SUPPLY")
        self.assertEqual(pedido.criado_por, self.usuario_loja)
        self.assertEqual(pedido.historico.count(), 1)

        self.client.force_login(self.usuario_outra_loja)
        resposta = self.client.get(reverse("pedidos:detalhe", args=[pedido.pk]))
        self.assertEqual(resposta.status_code, 404)

    def test_fluxo_com_ajustes_termina_na_separacao_parcial(self):
        pedido = self.criar_solicitacao("10")
        item = pedido.itens.get()

        resposta = self.executar_acao(
            self.supply, pedido, "iniciar-conferencia"
        )
        self.assertEqual(resposta.status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, "EM_CONFERENCIA")

        self.executar_acao(
            self.supply,
            pedido,
            "ajustar-supply",
            {f"item_{item.pk}": "8", "justificativa": "Ajuste do Supply"},
        )
        item.refresh_from_db()
        self.assertEqual(item.quantidade, Decimal("8"))

        self.executar_acao(
            self.supply,
            pedido,
            "encaminhar-aprovacao",
            {"observacao": "Conferido"},
        )
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, "AGUARDANDO_APROVACAO")
        self.assertEqual(pedido.conferido_por, self.supply)

        self.executar_acao(
            self.aprovador,
            pedido,
            "ajustar-aprovar",
            {f"item_{item.pk}": "7", "justificativa": "Limite aprovado"},
        )
        pedido.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(pedido.status, "APROVADO")
        self.assertEqual(item.quantidade_aprovada, Decimal("7"))

        self.executar_acao(self.separacao, pedido, "iniciar-separacao")
        self.executar_acao(
            self.separacao,
            pedido,
            "concluir-separacao",
            {f"item_{item.pk}": "6", "justificativa": "Uma caixa em falta"},
        )
        pedido.refresh_from_db()
        item.refresh_from_db()
        self.produto.refresh_from_db()
        self.assertEqual(pedido.status, "PARCIAL")
        self.assertEqual(item.quantidade_separada, Decimal("6"))
        self.assertEqual(self.produto.estoque_atual, Decimal("94"))
        self.assertIsNotNone(pedido.estoque_baixado_em)
        self.assertEqual(pedido.separado_por, self.separacao)
        self.assertEqual(Movimentacao.objects.filter(documento=f"PEDIDO-{pedido.pk}").count(), 1)
        self.assertEqual(Movimentacao.objects.get().quantidade, Decimal("6"))
        self.assertTrue(Romaneio.objects.filter(pedido=pedido, status="GERADO").exists())

        self.executar_acao(
            self.separacao,
            pedido,
            "concluir-separacao",
            {f"item_{item.pk}": "6", "justificativa": "Repetição"},
        )
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.estoque_atual, Decimal("94"))
        self.assertEqual(Movimentacao.objects.count(), 1)
        self.assertGreaterEqual(pedido.historico.count(), 7)

    def test_devolucoes_e_recusa_mantem_auditoria(self):
        pedido = self.criar_solicitacao()
        item = pedido.itens.get()
        self.executar_acao(self.supply, pedido, "iniciar-conferencia")
        self.executar_acao(
            self.supply,
            pedido,
            "devolver-loja",
            {"justificativa": "Quantidade precisa ser revisada"},
        )
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, "DEVOLVIDO_LOJA")

        self.executar_acao(
            self.usuario_loja,
            pedido,
            "reenviar-loja",
            {f"item_{item.pk}": "9", "justificativa": "Quantidade corrigida"},
        )
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, "ENVIADO_SUPPLY")

        self.executar_acao(self.supply, pedido, "iniciar-conferencia")
        self.executar_acao(self.supply, pedido, "encaminhar-aprovacao")
        self.executar_acao(
            self.aprovador,
            pedido,
            "devolver-supply-aprovador",
            {"justificativa": "Rever justificativa da loja"},
        )
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, "DEVOLVIDO_SUPPLY")

        self.executar_acao(self.supply, pedido, "iniciar-conferencia")
        self.executar_acao(
            self.supply,
            pedido,
            "recusar-supply",
            {"justificativa": "Solicitação fora da política"},
        )
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, "RECUSADO")
        self.assertIn("fora da política", pedido.motivo_ultima_acao)
        self.assertGreaterEqual(pedido.historico.count(), 9)

    def test_perfil_sem_permissao_nao_aprova(self):
        pedido = self.criar_solicitacao()
        resposta = self.executar_acao(self.usuario_loja, pedido, "aprovar")
        self.assertEqual(resposta.status_code, 403)
        pedido.refresh_from_db()
        self.assertEqual(pedido.status, "ENVIADO_SUPPLY")

    def test_estoque_insuficiente_bloqueia_separacao(self):
        pedido = self.criar_solicitacao("10")
        item = pedido.itens.get()
        self.executar_acao(self.supply, pedido, "iniciar-conferencia")
        self.executar_acao(self.supply, pedido, "encaminhar-aprovacao")
        self.executar_acao(self.aprovador, pedido, "aprovar")
        self.executar_acao(self.separacao, pedido, "iniciar-separacao")
        self.produto.estoque_atual = Decimal("5")
        self.produto.save(update_fields=["estoque_atual"])
        self.executar_acao(
            self.separacao,
            pedido,
            "concluir-separacao",
            {f"item_{item.pk}": "6", "justificativa": ""},
        )
        pedido.refresh_from_db()
        item.refresh_from_db()
        self.assertEqual(pedido.status, "EM_SEPARACAO")
        self.assertEqual(item.quantidade_separada, Decimal("0"))
        self.assertFalse(Movimentacao.objects.exists())
        self.assertFalse(Romaneio.objects.exists())

    def test_telas_mostram_apenas_acoes_da_etapa(self):
        pedido = self.criar_solicitacao("10")
        item = pedido.itens.get()

        self.client.force_login(self.supply)
        resposta = self.client.get(reverse("pedidos:detalhe", args=[pedido.pk]))
        self.assertContains(resposta, "Iniciar conferência")
        self.assertNotContains(resposta, "Aprovar sem alterações")

        self.executar_acao(self.supply, pedido, "iniciar-conferencia")
        resposta = self.client.get(reverse("pedidos:detalhe", args=[pedido.pk]))
        self.assertContains(resposta, "Conferir e enviar para aprovação")

        self.executar_acao(self.supply, pedido, "encaminhar-aprovacao")
        self.client.force_login(self.aprovador)
        resposta = self.client.get(reverse("pedidos:detalhe", args=[pedido.pk]))
        self.assertContains(resposta, "Aprovar sem alterações")
        self.assertNotContains(resposta, "Concluir separação")

        self.executar_acao(self.aprovador, pedido, "aprovar")
        self.client.force_login(self.separacao)
        resposta = self.client.get(reverse("pedidos:detalhe", args=[pedido.pk]))
        self.assertContains(resposta, "Iniciar separação")
        self.assertNotContains(resposta, "Concluir separação")

        self.executar_acao(self.separacao, pedido, "iniciar-separacao")
        resposta = self.client.get(reverse("pedidos:detalhe", args=[pedido.pk]))
        self.assertContains(resposta, "Concluir separação")

        self.executar_acao(
            self.separacao,
            pedido,
            "concluir-separacao",
            {f"item_{item.pk}": "10", "justificativa": ""},
        )
        resposta = self.client.get(reverse("pedidos:detalhe", args=[pedido.pk]))
        self.assertContains(resposta, "Separado")
        self.assertNotContains(resposta, "Confirmar expedição")

        resposta = self.executar_acao(self.separacao, pedido, "expedir")
        self.assertEqual(resposta.status_code, 403)

    def test_usuario_nao_autenticado_e_redirecionado_para_login(self):
        self.client.logout()
        resposta = self.client.get(reverse("pedidos:lista"))
        self.assertRedirects(
            resposta, f"{reverse('login')}?next={reverse('pedidos:lista')}"
        )
