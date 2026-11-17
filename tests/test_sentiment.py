from blogs_engenharia.nlp.sentiment import pontuar_sentimento_em_lote, rotulo_do_score

from .fakes import FakeSentimentClassifier


def test_pontuar_sentimento_em_lote_da_sinal_pelo_rotulo():
    classificador = FakeSentimentClassifier()

    scores = pontuar_sentimento_em_lote(classificador, ["This is a great release!", "This outage was a disaster."])

    assert scores == [0.95, -0.80]


def test_pontuar_sentimento_em_lote_trunca_antes_de_mandar_pro_modelo():
    classificador = FakeSentimentClassifier()
    # "great" só aparece depois do limite de truncamento — se o texto
    # não fosse cortado, o fake classificaria como POSITIVE.
    texto_longo = ("x" * 2500) + " great"

    scores = pontuar_sentimento_em_lote(classificador, [texto_longo])

    assert scores == [-0.80]


def test_rotulo_do_score_positivo():
    assert rotulo_do_score(0.9) == ("POSITIVE", 0.9)


def test_rotulo_do_score_negativo_vira_confianca_positiva():
    assert rotulo_do_score(-0.8) == ("NEGATIVE", 0.8)
