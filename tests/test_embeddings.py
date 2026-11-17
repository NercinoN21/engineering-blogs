import numpy as np

from blogs_engenharia.nlp.embeddings import gerar_embeddings, gerar_embeddings_por_post

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


def test_gerar_embeddings_por_post_devolve_um_vetor_por_post():
    modelo = FakeEmbeddingModel()

    embeddings = gerar_embeddings_por_post(modelo, [["abc", "xyz"], ["uvw"]])

    assert embeddings.shape == (2, 2)


def test_gerar_embeddings_por_post_e_a_media_normalizada_dos_pedacos():
    modelo = FakeEmbeddingModel()
    # "a" -> [1, 0] (1 vogal) e "b" -> [0, 1] (1 consoante): média [0.5, 0.5].
    embeddings = gerar_embeddings_por_post(modelo, [["a", "b"]])

    assert np.allclose(embeddings[0], [np.sqrt(0.5), np.sqrt(0.5)])
    assert np.isclose(np.linalg.norm(embeddings[0]), 1.0)
