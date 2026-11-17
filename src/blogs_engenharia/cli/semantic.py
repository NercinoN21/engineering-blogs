#!/usr/bin/env python3
"""Etapa 2 (PLN semântico): embeddings + sentimento sobre os posts já
coletados (`blogs-engenharia-scrape`), comparando convergência por
SIGNIFICADO — não só por palavra exata, como a Jaccard da etapa 1 — e
o tom das discussões (positivo/negativo).

Uso:
    blogs-engenharia-semantic              # roda tudo e mostra o resumo
    blogs-engenharia-semantic --limite 50  # só os 50 primeiros posts (teste rápido)

    # ou, sem instalar o pacote:
    python -m blogs_engenharia.cli.semantic

Pré-requisito: já ter rodado o scraper (precisa de posts em
data/posts.json). Mais lento que a etapa 1: carrega dois modelos
transformer (~90MB + ~260MB, baixados na 1ª execução) e roda os dois
sobre cada post.
"""

import argparse
import time

from blogs_engenharia.nlp.embeddings import carregar_modelo_embeddings, gerar_embeddings_por_post
from blogs_engenharia.nlp.pedacos import dividir_em_pedacos
from blogs_engenharia.nlp.resumo import carregar_segmentador_de_frases, extrair_resumo
from blogs_engenharia.nlp.semantic import (
    centroide_por_empresa,
    matriz_convergencia_semantica,
    sentimento_medio_por_empresa_ano,
)
from blogs_engenharia.nlp.sentiment import (
    carregar_classificador_sentimento,
    pontuar_sentimento_em_lote,
    rotulo_do_score,
)
from blogs_engenharia.scraper.database import get_db


def preparar_textos(posts: list[dict], segmentador) -> tuple[list[list[str]], list[str]]:
    """Os textos que cada modelo recebe: pedaços do post inteiro e o resumo.

    Cada modelo usa a entrada que mediu melhor na comparação das duas
    estratégias (ver README, "Resumo vs. post inteiro"): embeddings leem
    o post inteiro em pedaços; o sentimento lê só as 3 primeiras frases,
    porque os trechos técnicos do meio do post confundem o modelo
    treinado em resenhas de filme.
    """
    pedacos = [dividir_em_pedacos(segmentador, p["conteudo"]) for p in posts]
    resumos = [extrair_resumo(segmentador, p["conteudo"]) for p in posts]
    return pedacos, resumos


def processar_posts(posts, pedacos_por_post, resumos, modelo_embeddings, classificador) -> list[dict]:
    """Embeda (pelos pedaços) e classifica o sentimento (pelo resumo) de cada post.

    Devolve um registro por post com os campos originais (empresa, url,
    ano) mais o embedding e o sentimento — a entrada das agregações em
    `nlp/semantic.py`.
    """
    embeddings = gerar_embeddings_por_post(modelo_embeddings, pedacos_por_post)
    scores = pontuar_sentimento_em_lote(classificador, resumos)

    registros = []
    for post, embedding, score in zip(posts, embeddings, scores):
        label, confianca = rotulo_do_score(score)
        registros.append({
            "empresa": post["empresa"],
            "url": post["url"],
            "ano": post["data_publicacao"][:4],
            "embedding": embedding,
            "sentimento_label": label,
            "sentimento_score": confianca,
        })
    return registros


def salvar_resultados(db, matriz, sentimentos) -> None:
    """Salva a matriz de convergência semântica e o sentimento médio.

    Não salvamos os embeddings em si (ficariam pesados no TinyDB e não
    servem pra consulta direta) — só os resultados já agregados, mesmo
    espírito de `cli/analyze.py::salvar_resultados` na etapa 1.
    """
    db.table("semantic_convergencia").truncate()
    db.table("semantic_convergencia").insert_multiple(
        {"empresa_a": a, "empresa_b": b, "similaridade": round(score, 4)}
        for (a, b), score in matriz.items()
    )

    db.table("sentimento_por_empresa_ano").truncate()
    db.table("sentimento_por_empresa_ano").insert_multiple(
        {"empresa": empresa, "ano": ano, "score_medio": round(score, 4)}
        for (empresa, ano), score in sentimentos.items()
    )


def _imprimir_matriz_semantica(matriz: dict) -> None:
    print(f"\n{'=' * 80}\nMATRIZ DE CONVERGÊNCIA SEMÂNTICA (cosseno dos embeddings, 0=nada em comum, 1=idênticos)\n{'=' * 80}")
    empresas = sorted({e for par in matriz for e in par})
    header = " " * 11 + "".join(e[:9].rjust(11) for e in empresas)
    print(header)
    for a in empresas:
        linha = a.ljust(11)
        for b in empresas:
            par = (a, b) if (a, b) in matriz else (b, a)
            linha += f"{matriz.get(par, 1.0 if a == b else 0.0):.2f}".rjust(11)
        print(linha)


def _imprimir_sentimento(sentimentos: dict) -> None:
    print(f"\n{'=' * 80}\nSENTIMENTO MÉDIO POR EMPRESA E ANO (-1 = só negativo, +1 = só positivo)\n{'=' * 80}")
    empresas = sorted({empresa for empresa, _ in sentimentos})
    anos = sorted({ano for _, ano in sentimentos})
    header = "Empresa".ljust(10) + "".join(ano.rjust(8) for ano in anos)
    print(header)
    for empresa in empresas:
        linha = empresa.ljust(10)
        for ano in anos:
            valor = sentimentos.get((empresa, ano))
            linha += (f"{valor:+.2f}" if valor is not None else "   -").rjust(8)
        print(linha)


def imprimir_resumo(matriz: dict, sentimentos: dict) -> None:
    _imprimir_matriz_semantica(matriz)
    _imprimir_sentimento(sentimentos)


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

    print(f"Carregando modelos e processando {len(posts)} posts...")
    t0 = time.time()
    pedacos_por_post, resumos = preparar_textos(posts, carregar_segmentador_de_frases())
    print(f"{sum(map(len, pedacos_por_post))} pedaços de texto para os embeddings.")
    registros = processar_posts(
        posts, pedacos_por_post, resumos, carregar_modelo_embeddings(), carregar_classificador_sentimento()
    )
    print(f"Processamento concluído em {time.time() - t0:.1f}s.")

    centroides = centroide_por_empresa(registros)
    matriz = matriz_convergencia_semantica(centroides)
    sentimentos = sentimento_medio_por_empresa_ano(registros)

    salvar_resultados(db, matriz, sentimentos)
    imprimir_resumo(matriz, sentimentos)

    print(f"\nResultados salvos em data/posts.json, tabelas: "
          f"semantic_convergencia, sentimento_por_empresa_ano.")


if __name__ == "__main__":
    main()
