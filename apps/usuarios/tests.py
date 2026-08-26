from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from openpyxl import Workbook

from apps.lojas.models import Loja

from .importers import importar_logins_lojas
from .models import PerfilUsuario

Usuario = get_user_model()


def planilha_credenciais(linhas):
    pasta = Workbook()
    planilha = pasta.active
    planilha.title = "Credenciais"
    planilha.append(["ACESSOS"])
    planilha.append([])
    planilha.append(
        [
            "CÓDIGO DA LOJA",
            "NOME DA LOJA",
            "LOGIN",
            "SENHA TEMPORÁRIA",
        ]
    )
    for linha in linhas:
        planilha.append(linha)
    conteudo = BytesIO()
    pasta.save(conteudo)
    return conteudo.getvalue()


class ImportacaoLoginsTests(TestCase):
    def test_importa_loja_usuario_perfil_e_senha_temporaria(self):
        arquivo = BytesIO(
            planilha_credenciais(
                [["7601", "Sorocaba", "7601", "SenhaTemp@7601"]]
            )
        )

        resultado = importar_logins_lojas(arquivo)

        usuario = Usuario.objects.get(username="7601")
        loja = Loja.objects.get(codigo="7601")
        self.assertEqual(resultado.usuarios_criados, 1)
        self.assertTrue(usuario.check_password("SenhaTemp@7601"))
        self.assertEqual(usuario.perfil_insumos.papel, PerfilUsuario.LOJA)
        self.assertEqual(usuario.perfil_insumos.loja, loja)
        self.assertTrue(usuario.perfil_insumos.deve_trocar_senha)

    def test_nao_redefine_senha_existente_sem_confirmacao(self):
        loja = Loja.objects.create(codigo="7601", nome="Nome antigo")
        usuario = Usuario.objects.create_user(
            username="7601", password="SenhaAtual@7601"
        )
        PerfilUsuario.objects.create(
            usuario=usuario,
            papel=PerfilUsuario.LOJA,
            loja=loja,
        )
        arquivo = BytesIO(
            planilha_credenciais(
                [["7601", "Sorocaba", "7601", "SenhaNova@7601"]]
            )
        )

        resultado = importar_logins_lojas(arquivo)

        usuario.refresh_from_db()
        loja.refresh_from_db()
        self.assertEqual(resultado.usuarios_existentes, 1)
        self.assertEqual(resultado.senhas_redefinidas, 0)
        self.assertTrue(usuario.check_password("SenhaAtual@7601"))
        self.assertEqual(loja.nome, "Sorocaba")

    def test_importacao_pela_tela_e_redefinicao_explicita(self):
        administrador = Usuario.objects.create_superuser(
            username="admin", email="admin@example.com", password="Admin@123456"
        )
        loja = Loja.objects.create(codigo="7601", nome="Sorocaba")
        usuario = Usuario.objects.create_user(
            username="7601", password="SenhaAtual@7601"
        )
        PerfilUsuario.objects.create(
            usuario=usuario,
            papel=PerfilUsuario.LOJA,
            loja=loja,
        )
        upload = SimpleUploadedFile(
            "Logins_Lojas_FY27.xlsx",
            planilha_credenciais(
                [["7601", "Sorocaba", "7601", "SenhaNova@7601"]]
            ),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.client.force_login(administrador)

        resposta = self.client.post(
            reverse("usuarios:importar_logins"),
            {"arquivo": upload, "redefinir_senhas": "on"},
        )

        usuario.refresh_from_db()
        usuario.perfil_insumos.refresh_from_db()
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(usuario.check_password("SenhaNova@7601"))
        self.assertTrue(usuario.perfil_insumos.deve_trocar_senha)


class TrocaSenhaObrigatoriaTests(TestCase):
    def setUp(self):
        loja = Loja.objects.create(codigo="7601", nome="Sorocaba")
        self.usuario = Usuario.objects.create_user(
            username="7601", password="SenhaTemp@7601"
        )
        self.perfil = PerfilUsuario.objects.create(
            usuario=self.usuario,
            papel=PerfilUsuario.LOJA,
            loja=loja,
            deve_trocar_senha=True,
        )

    def test_redireciona_ate_usuario_trocar_a_senha(self):
        self.client.force_login(self.usuario)

        resposta = self.client.get(reverse("dashboard"))
        self.assertRedirects(resposta, reverse("usuarios:trocar_senha"))

        resposta = self.client.post(
            reverse("usuarios:trocar_senha"),
            {
                "old_password": "SenhaTemp@7601",
                "new_password1": "MinhaSenhaNova@7601",
                "new_password2": "MinhaSenhaNova@7601",
            },
        )
        self.assertRedirects(resposta, reverse("dashboard"))
        self.perfil.refresh_from_db()
        self.usuario.refresh_from_db()
        self.assertFalse(self.perfil.deve_trocar_senha)
        self.assertTrue(self.usuario.check_password("MinhaSenhaNova@7601"))


class PrivilegiosAdministradorTests(TestCase):
    def test_promove_adm_e_concede_acesso_total_ao_django_admin(self):
        usuario = Usuario.objects.create_user(username="novo-admin", password="Senha@123")

        perfil = PerfilUsuario.objects.create(
            usuario=usuario,
            papel=PerfilUsuario.ADMIN,
        )

        usuario.refresh_from_db()
        perfil.refresh_from_db()
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.is_superuser)
        self.assertTrue(perfil.privilegios_admin_gerenciados)
        self.client.force_login(usuario)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    def test_remove_adm_e_revoga_privilegios_concedidos_automaticamente(self):
        usuario = Usuario.objects.create_user(username="admin-temporario")
        perfil = PerfilUsuario.objects.create(
            usuario=usuario,
            papel=PerfilUsuario.ADMIN,
        )

        perfil.papel = PerfilUsuario.SUPPLY
        perfil.save()

        usuario.refresh_from_db()
        perfil.refresh_from_db()
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertFalse(perfil.privilegios_admin_gerenciados)

    def test_desativar_perfil_adm_revoga_privilegios_gerenciados(self):
        usuario = Usuario.objects.create_user(username="admin-inativo")
        perfil = PerfilUsuario.objects.create(
            usuario=usuario,
            papel=PerfilUsuario.ADMIN,
        )

        perfil.ativo = False
        perfil.save()

        usuario.refresh_from_db()
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)

    def test_superusuario_principal_e_preservado_ao_remover_papel_adm(self):
        usuario = Usuario.objects.create_superuser(
            username="admin-principal",
            email="principal@example.com",
            password="Senha@123",
        )
        perfil = PerfilUsuario.objects.create(
            usuario=usuario,
            papel=PerfilUsuario.ADMIN,
        )

        perfil.papel = PerfilUsuario.SUPPLY
        perfil.save()

        usuario.refresh_from_db()
        perfil.refresh_from_db()
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.is_superuser)
        self.assertFalse(perfil.privilegios_admin_gerenciados)
