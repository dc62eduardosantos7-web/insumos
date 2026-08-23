from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.estoque.models import ComposicaoKit, Movimentacao, Produto
from apps.lojas.models import Loja
from apps.romaneio.models import Romaneio
from apps.usuarios.models import PerfilUsuario

from .models import HistoricoPedido, ItemPedido, Pedido

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

    def criar_solicitacao(self, quantidade="10", usuario=None, produto=None):
        self.client.force_login(usuario or self.usuario_loja)
        produto = produto or self.produto
        resposta = self.client.post(
            reverse("pedidos:lista"),
            {
                "data": "2026-08-22",
                "observacoes": "Pedido de teste",
                "itens-TOTAL_FORMS": "1",
                "itens-INITIAL_FORMS": "0",
                "itens-MIN_NUM_FORMS": "0",
                "itens-MAX_NUM_FORMS": "1000",
                "itens-0-produto": str(produto.pk),
                "itens-0-quantidade": quantidade,
                "itens-0-observacao": "Urgente",
            },
        )
        self.assertEqual(resposta.status_code, 302)
        return Pedido.objects.latest("pk")

    def test_kit_e_expandido_e_baixa_estoque_dos_componentes(self):
        segundo_componente = Produto.objects.create(
            codigo="INS-KIT-002",
            nome="Segundo componente do kit",
            estoque_atual=Decimal("20"),
            unidade="UN",
        )
        kit = Produto.objects.create(
            codigo="KIT-TESTE",
            nome="KIT TESTE",
            categoria="KIT",
            unidade="UN",
        )
        ComposicaoKit.objects.create(
            kit=kit,
            item=self.produto,
            quantidade=Decimal("1"),
        )
        ComposicaoKit.objects.create(
            kit=kit,
            item=segundo_componente,
            quantidade=Decimal("2"),
        )

        pedido = self.criar_solicitacao("2", produto=kit)
        itens = list(pedido.itens.order_by("produto__codigo"))

        self.assertEqual(len(itens), 2)
        self.assertTrue(all(item.kit_origem == kit for item in itens))
        self.assertEqual(
            {item.produto_id: item.quantidade for item in itens},
            {
                self.produto.pk: Decimal("2"),
                segundo_componente.pk: Decimal("4"),
            },
        )

        self.executar_acao(self.supply, pedido, "iniciar-conferencia")
        self.executar_acao(self.supply, pedido, "encaminhar-aprovacao")
        self.executar_acao(self.aprovador, pedido, "aprovar")
        self.executar_acao(self.separacao, pedido, "iniciar-separacao")
        self.executar_acao(
            self.separacao,
            pedido,
            "concluir-separacao",
            {
                **{f"item_{item.pk}": str(item.quantidade) for item in itens},
                "justificativa": "",
            },
        )

        pedido.refresh_from_db()
        self.produto.refresh_from_db()
        segundo_componente.refresh_from_db()
        self.assertEqual(pedido.status, "SEPARADO")
        self.assertEqual(self.produto.estoque_atual, Decimal("98"))
        self.assertEqual(segundo_componente.estoque_atual, Decimal("16"))
        self.assertEqual(
            Movimentacao.objects.filter(documento=f"PEDIDO-{pedido.pk}").count(),
            2,
        )

        self.client.force_login(self.separacao)
        resposta = self.client.get(reverse("pedidos:detalhe", args=[pedido.pk]))
        self.assertContains(resposta, "Componente de KIT TESTE", count=2)

    def concluir_totalmente(self, pedido):
        item = pedido.itens.get()
        self.executar_acao(self.supply, pedido, "iniciar-conferencia")
        self.executar_acao(self.supply, pedido, "encaminhar-aprovacao")
        self.executar_acao(self.aprovador, pedido, "aprovar")
        self.executar_acao(self.separacao, pedido, "iniciar-separacao")
        self.executar_acao(
            self.separacao,
            pedido,
            "concluir-separacao",
            {f"item_{item.pk}": str(item.quantidade), "justificativa": ""},
        )
        pedido.refresh_from_db()
        return pedido

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
        self.assertTrue(
            Romaneio.objects.filter(
                pedidos=pedido, loja=self.loja, status="GERADO"
            ).exists()
        )

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

    def test_pedidos_da_mesma_loja_compartilham_um_romaneio(self):
        primeiro = self.concluir_totalmente(self.criar_solicitacao("4"))
        segundo = self.concluir_totalmente(self.criar_solicitacao("6"))

        self.assertEqual(Romaneio.objects.filter(loja=self.loja).count(), 1)
        romaneio = Romaneio.objects.get(loja=self.loja)
        self.assertEqual(primeiro.romaneio, romaneio)
        self.assertEqual(segundo.romaneio, romaneio)
        self.assertEqual(
            list(romaneio.pedidos.order_by("pk")),
            [primeiro, segundo],
        )

        self.client.force_login(self.separacao)
        resposta = self.client.get(reverse("romaneio:imprimir", args=[romaneio.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "ROMANEIO CONSOLIDADO DE INSUMOS")
        self.assertContains(resposta, f"#{primeiro.pk}")
        self.assertContains(resposta, f"#{segundo.pk}")
        self.assertContains(resposta, ">10<", html=False)

    def test_lojas_diferentes_recebem_romaneios_diferentes(self):
        primeiro = self.concluir_totalmente(self.criar_solicitacao("3"))
        segundo = self.concluir_totalmente(
            self.criar_solicitacao("2", usuario=self.usuario_outra_loja)
        )

        self.assertEqual(Romaneio.objects.count(), 2)
        self.assertNotEqual(primeiro.romaneio_id, segundo.romaneio_id)
        self.assertEqual(primeiro.romaneio.loja, self.loja)
        self.assertEqual(segundo.romaneio.loja, self.outra_loja)

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


class AdminExclusaoTotalTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser(
            username="admin-exclusao",
            email="admin@example.com",
            password="teste123",
        )
        self.client.force_login(self.admin)
        self.loja = Loja.objects.create(
            codigo="900", nome="Loja Teste Admin", lane="90"
        )
        self.produto = Produto.objects.create(
            codigo="INS-900",
            nome="Produto Teste Admin",
            estoque_atual=Decimal("50"),
            unidade="UN",
        )

    def criar_dados(self):
        romaneio = Romaneio.objects.create(loja=self.loja)
        pedido = Pedido.objects.create(
            loja=self.loja,
            romaneio=romaneio,
            lane=self.loja.lane,
            status="SEPARADO",
            criado_por=self.admin,
        )
        ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade=Decimal("2"),
            quantidade_separada=Decimal("2"),
        )
        HistoricoPedido.objects.create(
            pedido=pedido,
            acao="Pedido separado",
            status_novo="SEPARADO",
            usuario=self.admin,
        )
        return pedido, romaneio

    def test_admin_exibe_botao_nas_duas_paginas(self):
        resposta = self.client.get(reverse("admin:pedidos_pedido_changelist"))
        self.assertContains(resposta, "Excluir tudo")

        resposta = self.client.get(reverse("admin:romaneio_romaneio_changelist"))
        self.assertContains(resposta, "Excluir tudo")

    def test_excluir_todos_pedidos_preserva_base_cadastral(self):
        _pedido, romaneio = self.criar_dados()
        url = reverse("admin:pedidos_pedido_excluir_tudo")

        resposta = self.client.post(url, {"confirmacao": "sim"})

        self.assertRedirects(resposta, reverse("admin:pedidos_pedido_changelist"))
        self.assertFalse(Pedido.objects.exists())
        self.assertFalse(ItemPedido.objects.exists())
        self.assertFalse(HistoricoPedido.objects.exists())
        self.assertTrue(Romaneio.objects.filter(pk=romaneio.pk).exists())
        self.assertTrue(Loja.objects.filter(pk=self.loja.pk).exists())
        self.assertTrue(Produto.objects.filter(pk=self.produto.pk).exists())
        self.assertTrue(Usuario.objects.filter(pk=self.admin.pk).exists())

    def test_excluir_romaneios_desvincula_e_preserva_pedidos(self):
        pedido, _romaneio = self.criar_dados()
        url = reverse("admin:romaneio_romaneio_excluir_tudo")

        resposta = self.client.post(url, {"confirmacao": "sim"})

        self.assertRedirects(
            resposta, reverse("admin:romaneio_romaneio_changelist")
        )
        self.assertFalse(Romaneio.objects.exists())
        pedido.refresh_from_db()
        self.assertIsNone(pedido.romaneio_id)
        self.assertTrue(Loja.objects.filter(pk=self.loja.pk).exists())
        self.assertTrue(Produto.objects.filter(pk=self.produto.pk).exists())

    def test_confirmacao_e_obrigatoria(self):
        self.criar_dados()
        url = reverse("admin:pedidos_pedido_excluir_tudo")

        resposta = self.client.post(url, {})

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta, "Marque a confirmação antes de excluir os registros."
        )
        self.assertTrue(Pedido.objects.exists())
