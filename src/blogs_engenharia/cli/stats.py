#!/usr/bin/env python3
"""Pequeno script de conferência: mostra quantos posts foram coletados,
por empresa e por ano, lendo direto do TinyDB.

Não faz parte da análise do projeto (a pergunta de pesquisa usa
embeddings/similaridade, que fica para a próxima etapa) — serve só para
verificar rapidamente que a coleta funcionou como esperado.

Uso: blogs-engenharia-stats (ou `python -m blogs_engenharia.cli.stats`)
"""

from collections import Counter

from blogs_engenharia.scraper.config import DB_PATH
from blogs_engenharia.scraper.database import get_db


def main():
    db = get_db()
    posts = db.all()

    if not posts:
        print(f"Nenhum post encontrado em {DB_PATH}. Rode 'blogs-engenharia-scrape' primeiro.")
        return

    print(f"Total de posts no banco: {len(posts)}\n")

    por_empresa = Counter(p["empresa"] for p in posts)
    print("Posts por empresa:")
    for empresa, qtd in sorted(por_empresa.items(), key=lambda kv: -kv[1]):
        print(f"  {empresa:10s}: {qtd}")

    print("\nPosts por empresa e ano:")
    por_empresa_ano = Counter((p["empresa"], p["data_publicacao"][:4]) for p in posts)
    empresas = sorted(por_empresa)
    anos = sorted({ano for _, ano in por_empresa_ano})
    header = "Empresa".ljust(10) + "".join(ano.rjust(6) for ano in anos)
    print(header)
    for empresa in empresas:
        linha = empresa.ljust(10)
        for ano in anos:
            linha += str(por_empresa_ano.get((empresa, ano), 0)).rjust(6)
        print(linha)

    tamanhos = [len(p["conteudo"]) for p in posts]
    print(f"\nTamanho do conteúdo (caracteres): min={min(tamanhos)}, "
          f"médio={sum(tamanhos)//len(tamanhos)}, máx={max(tamanhos)}")

    vazios = [p["url"] for p in posts if len(p["conteudo"]) < 200]
    if vazios:
        print(f"\nAtenção: {len(vazios)} posts com conteúdo suspeitosamente curto (<200 caracteres):")
        for u in vazios[:10]:
            print(f"  {u}")


if __name__ == "__main__":
    main()
