import numpy as np

from blogs_engenharia.nlp.embeddings import gerar_embeddings

from .fakes import FakeEmbeddingModel


def test_gerar_embeddings_devolve_uma_linha_por_texto():
    modelo = FakeEmbeddingModel()

    embeddings = gerar_embeddings(modelo, ["abc", "xyz uvw"])

    assert embeddings.shape == (2, 2)


def test_gerar_embeddings_e_deterministico_para_o_mesmo_texto():
    modelo = FakeEmbeddingModel()

    a = gerar_embeddings(modelo, ["mesmo texto"])
    b = gerar_embeddings(modelo, ["mesmo texto"])

    assert np.array_equal(a, b)
