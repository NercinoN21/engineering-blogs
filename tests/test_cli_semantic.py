import pytest

from blogs_engenharia.cli.semantic import preparar_textos, processar_posts
from blogs_engenharia.nlp.resumo import carregar_segmentador_de_frases

from .fakes import FakeEmbeddingModel, FakeSentimentClassifier

POST = {
    "empresa": "Slack",
    "url": "https://slack.engineering/x",
    "data_publicacao": "2024-05-01",
    "conteudo": "Intro sentence. Second one. Third one. This great ending is the fourth.",
}


def test_preparar_textos_pedacos_leem_o_post_inteiro():
    pedacos, _ = preparar_textos([POST], carregar_segmentador_de_frases())

    assert "fourth" in " ".join(pedacos[0])


def test_preparar_textos_resumo_usa_so_as_tres_primeiras_frases():
    _, resumos = preparar_textos([POST], carregar_segmentador_de_frases())

    assert resumos == ["Intro sentence. Second one. Third one."]


def test_processar_posts_sentimento_vem_do_resumo_nao_dos_pedacos():
    # "great" só aparece nos pedaços; o resumo não tem -> NEGATIVE.
    pedacos, resumos = [["This is great."]], ["Outage report."]

    [registro] = processar_posts([POST], pedacos, resumos, FakeEmbeddingModel(), FakeSentimentClassifier())

    assert registro["sentimento_label"] == "NEGATIVE"
    assert registro["sentimento_score"] == pytest.approx(0.80)
    assert registro["ano"] == "2024"
    assert registro["embedding"].shape == (2,)
