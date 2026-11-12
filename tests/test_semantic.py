import numpy as np
import pytest

from blogs_engenharia.nlp.semantic import (
    centroide_por_empresa,
    matriz_convergencia_semantica,
    sentimento_medio_por_empresa_ano,
    similaridade_cosseno,
)


def test_centroide_por_empresa_tira_a_media_dos_embeddings():
    registros = [
        {"empresa": "Uber", "embedding": np.array([1.0, 0.0])},
        {"empresa": "Uber", "embedding": np.array([0.0, 1.0])},
    ]

    centroides = centroide_por_empresa(registros)

    assert np.allclose(centroides["Uber"], [0.5, 0.5])


def test_similaridade_cosseno_vetores_identicos_e_um():
    assert similaridade_cosseno(np.array([1.0, 2.0]), np.array([1.0, 2.0])) == pytest.approx(1.0)


def test_similaridade_cosseno_vetores_perpendiculares_e_zero():
    assert similaridade_cosseno(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == 0.0


def test_similaridade_cosseno_com_vetor_nulo_nao_quebra():
    assert similaridade_cosseno(np.array([0.0, 0.0]), np.array([1.0, 1.0])) == 0.0


def test_matriz_convergencia_semantica_calcula_pares():
    centroides = {"A": np.array([1.0, 0.0]), "B": np.array([1.0, 0.0]), "C": np.array([0.0, 1.0])}

    matriz = matriz_convergencia_semantica(centroides)

    assert matriz[("A", "B")] == 1.0
    assert matriz[("A", "C")] == 0.0


def test_sentimento_medio_por_empresa_ano_combina_sinal_e_score():
    registros = [
        {"empresa": "Meta", "ano": "2026", "sentimento_label": "POSITIVE", "sentimento_score": 0.8},
        {"empresa": "Meta", "ano": "2026", "sentimento_label": "NEGATIVE", "sentimento_score": 0.4},
    ]

    medias = sentimento_medio_por_empresa_ano(registros)

    assert medias[("Meta", "2026")] == 0.2
