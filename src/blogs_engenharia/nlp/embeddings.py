"""Embeddings semânticos dos posts (etapa 2): representa cada resumo de
post como um vetor, permitindo comparar empresas por SIGNIFICADO em vez
de só por palavra exata (como a similaridade de Jaccard da etapa 1).

Modelo: `all-MiniLM-L6-v2` (sentence-transformers) — ~90MB, rápido o
bastante pra rodar em CPU sobre ~1.150 posts em poucos minutos, e é o
modelo mais usado em tutoriais de similaridade semântica (bom ponto de
partida pra quem está vendo isso pela primeira vez).
"""

import numpy as np

from blogs_engenharia.nlp.pedacos import achatar, reagrupar

MODELO_EMBEDDINGS = "all-MiniLM-L6-v2"


def carregar_modelo_embeddings():
    """Carrega o modelo de sentence-transformers (baixado na 1ª execução).

    Import adiado pra dentro da função: carregar o pacote inteiro (e o
    torch que ele arrasta) só quando alguém realmente pede o modelo,
    mesma ideia de `scraper/utils.py::make_driver` com o Selenium.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODELO_EMBEDDINGS)


def gerar_embeddings(modelo, textos: list[str]):
    """Converte uma lista de textos numa matriz de vetores (um por linha).

    `modelo` é injetável em vez de criado aqui dentro: em produção é o
    `SentenceTransformer` real; nos testes, um fake com `.encode()` que
    não baixa nada (ver `tests/fakes.py::FakeEmbeddingModel`).
    `normalize_embeddings=True` deixa os vetores com norma 1, o que
    simplifica a similaridade de cosseno depois (`nlp/semantic.py`).
    """
    return modelo.encode(textos, show_progress_bar=False, normalize_embeddings=True)


def gerar_embeddings_por_post(modelo, pedacos_por_post: list[list[str]]) -> np.ndarray:
    """Um vetor por post: a média dos embeddings dos seus pedaços, renormalizada.

    Todos os pedaços vão ao modelo numa chamada só (bem mais rápido que
    uma por post). A média é renormalizada para norma 1, mantendo a
    mesma escala dos vetores de `gerar_embeddings`.
    Exemplo:
        gerar_embeddings_por_post(modelo, [["p1", "p2"], ["p3"]])  # -> matriz 2 x 384
    """
    textos, tamanhos = achatar(pedacos_por_post)
    vetores = gerar_embeddings(modelo, textos)
    medias = np.array([np.mean(grupo, axis=0) for grupo in reagrupar(vetores, tamanhos)])
    normas = np.linalg.norm(medias, axis=1, keepdims=True)
    return medias / np.where(normas == 0, 1.0, normas)
