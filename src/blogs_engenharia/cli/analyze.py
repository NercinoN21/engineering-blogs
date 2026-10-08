#!/usr/bin/env python3
"""Etapa 1 (PLN): roda RE + spaCy sobre os posts já coletados pelo
scraper (`blogs-engenharia-scrape`) e salva/mostra uma análise de
convergência e divergência temática entre os blogs de engenharia.

Uso:
    blogs-engenharia-analyze              # roda tudo e mostra o resumo
    blogs-engenharia-analyze --limite 50  # só os 50 primeiros posts (teste rápido)

    # ou, sem instalar o pacote:
    python -m blogs_engenharia.cli.analyze

Pré-requisito: já ter rodado o scraper pelo menos uma vez (precisa de
posts salvos em data/posts.json).
"""

import argparse
import time
from collections import Counter

from blogs_engenharia.nlp.aggregate import (
    TERMOS_QUENTES,
    agregar_por_empresa,
    agregar_por_empresa_ano,
    evolucao_termos,
    matriz_convergencia,
    top_termos,
)
from blogs_engenharia.nlp.pipeline import carregar_modelo, processar_posts
from blogs_engenharia.scraper.database import get_db


def salvar_resultados(db, registros, por_empresa, matriz, evolucao):
    db.table("nlp_termos_por_post").truncate()
    db.table("nlp_termos_por_post").insert_multiple(
        {"empresa": r["empresa"], "url": r["url"], "ano": r["ano"],
         "top_lemas": top_termos(Counter(r["lemas"]), 10),
         "entidades": r["entidades"][:10], "siglas": r["siglas"][:10]}
        for r in registros
    )

    db.table("nlp_resumo_empresa").truncate()
    db.table("nlp_resumo_empresa").insert_multiple(
        {"empresa": empresa, "top_termos": top_termos(contador, 20)}
        for empresa, contador in por_empresa.items()
    )

    db.table("nlp_convergencia").truncate()
    db.table("nlp_convergencia").insert_multiple(
        {"empresa_a": a, "empresa_b": b, "jaccard": score} for (a, b), score in matriz.items()
    )

    db.table("nlp_evolucao_termos").truncate()
    linhas = []
    for termo, por_empresa_ano in evolucao.items():
        for (empresa, ano), freq in por_empresa_ano.items():
            linhas.append({"termo": termo, "empresa": empresa, "ano": ano, "freq_por_mil": freq})
    db.table("nlp_evolucao_termos").insert_multiple(linhas)


def imprimir_resumo(por_empresa, matriz, evolucao):
    print(f"\n{'=' * 70}\nTOP 10 TERMOS POR EMPRESA\n{'=' * 70}")
    for empresa, contador in sorted(por_empresa.items()):
        termos = ", ".join(f"{t}({f})" for t, f in top_termos(contador, 10))
        print(f"  {empresa:10s}: {termos}")

    print(f"\n{'=' * 70}\nMATRIZ DE CONVERGÊNCIA (Jaccard dos top-50 termos, 0=nada em comum, 1=idênticos)\n{'=' * 70}")
    empresas = sorted({e for par in matriz for e in par})
    header = " " * 11 + "".join(e[:9].rjust(11) for e in empresas)
    print(header)
    for a in empresas:
        linha = a.ljust(11)
        for b in empresas:
            par = (a, b) if (a, b) in matriz else (b, a)
            linha += f"{matriz.get(par, 1.0 if a == b else 0.0):.2f}".rjust(11)
        print(linha)

    print(f"\n{'=' * 70}\nEVOLUÇÃO DE TERMOS QUENTES (ocorrências por mil termos relevantes, por ano, somando as empresas)\n{'=' * 70}")
    anos = sorted({ano for d in evolucao.values() for (_, ano) in d})
    header = "Termo".ljust(14) + "".join(ano.rjust(8) for ano in anos)
    print(header)
    for termo in TERMOS_QUENTES:
        por_empresa_ano = evolucao[termo]
        linha = termo.ljust(14)
        for ano in anos:
            valores_do_ano = [v for (emp, a), v in por_empresa_ano.items() if a == ano]
            media = sum(valores_do_ano) / len(valores_do_ano) if valores_do_ano else 0.0
            linha += f"{media:.1f}".rjust(8)
        print(linha)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limite", type=int, default=None, help="processar só os N primeiros posts (teste rápido)")
    args = parser.parse_args()

    db = get_db()
    posts = db.all()
    if args.limite:
        posts = posts[: args.limite]
    if not posts:
        print("Nenhum post encontrado. Rode 'blogs-engenharia-scrape' primeiro.")
        return

    print(f"Carregando modelo spaCy (en_core_web_sm) e processando {len(posts)} posts...")
    t0 = time.time()
    nlp = carregar_modelo()
    registros = list(processar_posts(posts, nlp))
    print(f"Processamento concluído em {time.time() - t0:.1f}s.")

    por_empresa = agregar_por_empresa(registros)
    por_empresa_ano = agregar_por_empresa_ano(registros)
    matriz = matriz_convergencia(por_empresa)
    evolucao = evolucao_termos(por_empresa_ano)

    salvar_resultados(db, registros, por_empresa, matriz, evolucao)
    imprimir_resumo(por_empresa, matriz, evolucao)

    print(f"\nResultados salvos em data/posts.json, tabelas: "
          f"nlp_termos_por_post, nlp_resumo_empresa, nlp_convergencia, nlp_evolucao_termos.")


if __name__ == "__main__":
    main()
