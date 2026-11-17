"""Agregação e métricas da análise semântica (etapa 2): combina os
embeddings e sentimentos post a post em estatísticas por empresa/ano, e
calcula a versão semântica da matriz de convergência da etapa 1.

Como `aggregate.py` (etapa 1), este módulo é só matemática pura sobre
dados já calculados — nenhuma chamada a modelo aqui, pra poder testar
rápido com vetores/números falsos (ver `tests/test_semantic.py`).
"""

from collections import defaultdict

import numpy as np


def centroide_por_empresa(registros: list[dict]) -> dict[str, np.ndarray]:
    """Vetor médio (centróide) dos embeddings de cada empresa.

    O centróide resume "sobre o que a empresa fala, em média" num único
    ponto do espaço semântico — é o que comparamos entre empresas na
    matriz de convergência semântica, análogo ao top-50 de termos usado
    na Jaccard da etapa 1.
    """
    por_empresa = defaultdict(list)
    for r in registros:
        por_empresa[r["empresa"]].append(r["embedding"])
    return {empresa: np.mean(vetores, axis=0) for empresa, vetores in por_empresa.items()}


def similaridade_cosseno(a: np.ndarray, b: np.ndarray) -> float:
    """Similaridade de cosseno entre dois vetores.

    1 = mesma direção (mesmo assunto, em significado), 0 = direções
    perpendiculares (assuntos não relacionados). Diferente da Jaccard da
    etapa 1, não exige palavra idêntica — só proximidade de sentido.
    """
    norma_a, norma_b = np.linalg.norm(a), np.linalg.norm(b)
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norma_a * norma_b))


def matriz_convergencia_semantica(centroides: dict[str, np.ndarray]) -> dict[tuple[str, str], float]:
    """Similaridade de cosseno entre os centróides de cada par de empresas.

    Versão semântica da `matriz_convergencia` (Jaccard) da etapa 1: mede
    convergência por significado em vez de por palavra exata.
    """
    empresas = sorted(centroides)
    matriz = {}
    for i, a in enumerate(empresas):
        for b in empresas[i:]:
            matriz[(a, b)] = similaridade_cosseno(centroides[a], centroides[b])
    return matriz


def sentimento_medio_por_empresa_ano(registros: list[dict]) -> dict[tuple[str, str], float]:
    """Score médio de sentimento (-1 a 1) por empresa e ano.

    `sentimento_score` de cada post já vem com sinal (P(POSITIVO) −
    P(NEGATIVO), ver `sentiment.py::tom_do_post`) — a média por
    empresa/ano mostra para que lado o tom pende naquele período.
    Complementa `evolucao_termos` da etapa 1, que mostra SOBRE O QUE se
    fala, não COM QUE TOM.
    """
    por_empresa_ano = defaultdict(list)
    for r in registros:
        por_empresa_ano[(r["empresa"], r["ano"])].append(r["sentimento_score"])
    return {chave: sum(v) / len(v) for chave, v in por_empresa_ano.items()}


def distribuicao_tom_por_empresa(registros: list[dict]) -> dict[str, dict[str, float]]:
    """Fração dos posts de cada empresa em cada tom (POSITIVO/NEUTRO/NEGATIVO).

    A média de `sentimento_medio_por_empresa_ano` esconde quantos posts
    são neutros; esta tabela mostra a proporção de cada tom.
    Exemplo:
        distribuicao_tom_por_empresa(registros)["Meta"]  # -> {"POSITIVO": 0.5, "NEUTRO": 0.4, "NEGATIVO": 0.1}
    """
    tons_por_empresa = defaultdict(list)
    for r in registros:
        tons_por_empresa[r["empresa"]].append(r["sentimento_label"])
    return {
        empresa: {tom: tons.count(tom) / len(tons) for tom in ("POSITIVO", "NEUTRO", "NEGATIVO")}
        for empresa, tons in tons_por_empresa.items()
    }
