import re

from django.db import transaction
from pypdf import PdfReader

from .models import Loja


PADRAO_LOJA = re.compile(
    r"(?:^|\s)(?P<lane>\d{1,2})\s+"
    r"(?P<codigo>\d{4,5})\s*-\s*"
    r"(?P<nome>.*?)"
    r"(?=\s+\d{1,2}\s+\d{4,5}\s*-|\s*$)"
)


def _texto(valor):
    return re.sub(r"\s+", " ", str(valor or "")).strip()


def _extrair_lojas(arquivo):
    reader = PdfReader(arquivo)
    registros = {}
    ocorrencias = 0
    divergencias = []

    for numero_pagina, pagina in enumerate(reader.pages, start=1):
        texto = pagina.extract_text(extraction_mode="layout") or ""
        for linha in texto.splitlines():
            for encontrado in PADRAO_LOJA.finditer(linha):
                ocorrencias += 1
                codigo = encontrado.group("codigo")
                nome = _texto(encontrado.group("nome"))
                lane = str(int(encontrado.group("lane")))
                if not nome:
                    continue

                registro = registros.setdefault(
                    codigo, {"nome": nome, "lanes": set(), "pagina": numero_pagina}
                )
                registro["lanes"].add(lane)
                if registro["nome"].casefold() != nome.casefold():
                    divergencias.append(
                        f"Código {codigo}: nomes diferentes no cronograma "
                        f"('{registro['nome']}' e '{nome}'). Foi mantido o primeiro."
                    )

    if not registros:
        raise ValueError(
            "Nenhuma loja foi localizada. Verifique se o PDF contém texto e as "
            "colunas Lane e Loja no mesmo formato do cronograma fornecido."
        )

    return registros, ocorrencias, divergencias


def importar_cronograma_pdf(arquivo):
    registros, ocorrencias, divergencias = _extrair_lojas(arquivo)
    criados = atualizados = sem_alteracao = 0
    multiplas_lanes = 0

    for codigo, dados in registros.items():
        lanes = sorted(dados["lanes"], key=int)
        lane = " / ".join(lanes)
        if len(lanes) > 1:
            multiplas_lanes += 1

        with transaction.atomic():
            loja = Loja.objects.filter(codigo__iexact=codigo).first()
            if loja is None:
                Loja.objects.create(codigo=codigo, nome=dados["nome"], lane=lane)
                criados += 1
                continue

            campos = []
            if loja.nome != dados["nome"]:
                loja.nome = dados["nome"]
                campos.append("nome")
            if loja.lane != lane:
                loja.lane = lane
                campos.append("lane")
            if campos:
                loja.save(update_fields=campos + ["atualizado_em"])
                atualizados += 1
            else:
                sem_alteracao += 1

    return {
        "ocorrencias": ocorrencias,
        "lojas": len(registros),
        "criados": criados,
        "atualizados": atualizados,
        "sem_alteracao": sem_alteracao,
        "multiplas_lanes": multiplas_lanes,
        "divergencias": divergencias,
    }
