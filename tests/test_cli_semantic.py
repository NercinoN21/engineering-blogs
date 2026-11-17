import pytest

from blogs_engenharia.cli.semantic import processar_posts

from .fakes import FakeEmbeddingModel, FakeZeroShotClassifier

POST = {
    "empresa": "Slack",
    "url": "https://slack.engineering/x",
    "data_publicacao": "2024-05-01",
    "conteudo": "irrelevante: os pedaços são passados prontos",
}


def test_processar_posts_combina_o_tom_dos_pedacos():
    pedacos_por_post = [["A great launch.", "The outage was bad.", "We use Kafka."]]

    [registro] = processar_posts([POST], pedacos_por_post, FakeEmbeddingModel(), FakeZeroShotClassifier())

    # cada tom ganha 0.8 em um pedaço: médias empatadas em 0.333,
    # então o score P(POS) − P(NEG) fica em zero.
    assert registro["sentimento_score"] == pytest.approx(0.0)
    assert registro["ano"] == "2024"
    assert registro["embedding"].shape == (2,)


def test_processar_posts_um_registro_por_post():
    posts = [POST, {**POST, "url": "https://slack.engineering/y"}]

    registros = processar_posts(posts, [["Great."], ["Outage."]], FakeEmbeddingModel(), FakeZeroShotClassifier())

    assert [r["sentimento_label"] for r in registros] == ["POSITIVO", "NEGATIVO"]
