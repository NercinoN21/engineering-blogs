from blogs_engenharia.nlp.sentiment import classificar_sentimento

from .fakes import FakeSentimentClassifier


def test_classificar_sentimento_repassa_rotulo_positivo():
    classificador = FakeSentimentClassifier()

    label, score = classificar_sentimento(classificador, "This is a great release!")

    assert label == "POSITIVE"
    assert score == 0.95


def test_classificar_sentimento_repassa_rotulo_negativo():
    classificador = FakeSentimentClassifier()

    label, score = classificar_sentimento(classificador, "This outage was a disaster.")

    assert label == "NEGATIVE"
    assert score == 0.80


def test_classificar_sentimento_trunca_antes_de_mandar_pro_modelo():
    classificador = FakeSentimentClassifier()
    # "great" só aparece depois do limite de truncamento — se o texto
    # não fosse cortado, o fake classificaria como POSITIVE.
    texto_longo = ("x" * 2500) + " great"

    label, _ = classificar_sentimento(classificador, texto_longo)

    assert label == "NEGATIVE"
