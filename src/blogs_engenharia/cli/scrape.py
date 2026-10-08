#!/usr/bin/env python3
"""Ponto de entrada do projeto: raspa os 7 blogs de engenharia e salva
tudo no TinyDB (data/posts.json).

Uso:
    blogs-engenharia-scrape                     # roda todos os blogs
    blogs-engenharia-scrape --blogs slack meta  # roda só alguns
    blogs-engenharia-scrape --list              # lista os nomes válidos de --blogs

    # ou, sem instalar o pacote:
    python -m blogs_engenharia.cli.scrape

Cada coletor é independente (vive em scraper/blogs/<nome>.py) e sabe
evitar duplicatas sozinho (scraper/database.py faz upsert por URL), então
é seguro rodar este script várias vezes.

Nota: Dropbox, Netflix e Airbnb foram testados e removidos da lista
padrão por renderem amostras pequenas demais na janela de 5 anos (10-29
posts, contra 78-1127 dos demais) — Netflix/Airbnb por causa do limite
de paginação do RSS do Medium, Dropbox por causa de um bloqueio AWS WAF
agressivo. Ver README.md para os detalhes.
"""

import argparse

from blogs_engenharia.scraper import config
from blogs_engenharia.scraper.blogs import github, meta, microsoft, shopify, slack, spotify, uber
from blogs_engenharia.scraper.database import get_db

COLETORES = {
    "slack": slack.collect,
    "spotify": spotify.collect,
    "uber": uber.collect,
    "meta": meta.collect,
    "microsoft": microsoft.collect,
    "github": github.collect,
    "shopify": shopify.collect,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--blogs",
        nargs="+",
        choices=sorted(COLETORES),
        default=sorted(COLETORES),
        help="quais blogs raspar (padrão: todos)",
    )
    parser.add_argument("--list", action="store_true", help="só lista os blogs disponíveis e sai")
    args = parser.parse_args()

    if args.list:
        for nome in sorted(COLETORES):
            print(nome)
        return

    print(f"Janela temporal da amostra: últimos {config.JANELA_EM_ANOS} anos "
          f"(a partir de {config.CUTOFF_DATE.isoformat()})")
    print(f"Banco de dados: {config.DB_PATH}\n")

    db = get_db()
    totais = {}
    for nome in args.blogs:
        print(f"\n{'=' * 60}\n{nome.upper()}\n{'=' * 60}")
        try:
            totais[nome] = COLETORES[nome](db)
        except Exception as exc:  # um blog falhar não deve derrubar os outros
            print(f"[{nome}] ERRO não tratado: {exc}")
            totais[nome] = 0

    print(f"\n{'=' * 60}\nRESUMO\n{'=' * 60}")
    for nome, qtd in totais.items():
        print(f"  {nome:10s}: {qtd} posts novos/atualizados nesta execução")
    print(f"\nTotal de documentos no banco agora: {len(db)}")


if __name__ == "__main__":
    main()
