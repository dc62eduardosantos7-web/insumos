from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.estoque.importers import importar_produtos_xlsx


class Command(BaseCommand):
    help = "Importa produtos de uma planilha XLSX e ajusta o saldo ao campo TOTAL."

    def add_arguments(self, parser):
        parser.add_argument(
            "arquivo",
            nargs="?",
            default=str(Path(settings.BASE_DIR) / "dados" / "Pasta1.xlsx"),
        )

    def handle(self, *args, **options):
        caminho = Path(options["arquivo"])
        if not caminho.exists():
            raise CommandError(f"Arquivo não encontrado: {caminho}")

        with caminho.open("rb") as arquivo:
            resultado = importar_produtos_xlsx(
                arquivo,
                nome_arquivo=caminho.name,
            )

        self.stdout.write(self.style.SUCCESS("Importação concluída."))
        self.stdout.write(f"Aba: {resultado['aba']}")
        self.stdout.write(f"Linhas válidas: {resultado['linhas_validas']}")
        self.stdout.write(f"Produtos importados: {resultado['produtos_importados']}")
        self.stdout.write(f"Criados: {resultado['criados']}")
        self.stdout.write(f"Atualizados: {resultado['atualizados']}")
        self.stdout.write(f"Sem alteração: {resultado['sem_alteracao']}")
        self.stdout.write(
            "Repetidos com menor estoque descartados: "
            f"{resultado['descartados_menor_estoque']}"
        )
        self.stdout.write(
            f"Cadastros antigos excluídos: {resultado['excluidos_existentes']}"
        )
        self.stdout.write(
            f"Cadastros antigos inativados por possuírem uso: {resultado['inativados_por_uso']}"
        )
        self.stdout.write(f"Ignorados: {resultado['ignorados']}")
        self.stdout.write(f"Erros: {len(resultado['erros'])}")
        for erro in resultado["erros"][:20]:
            self.stderr.write(erro)
