import pytest

from blogs_engenharia.nlp.sentiment import LIMITE_CARACTERES, probabilidades_em_lote, tom_do_post

from .fakes import FakeZeroShotClassifier


def test_probabilidades_em_lote_traduz_rotulos_para_tons():
    classificador = FakeZeroShotClassifier()

    [conquista, problema, neutro] = probabilidades_em_lote(
        classificador, ["A great release!", "The outage hit users.", "We use Kafka."]
    )

    assert conquista == {"POSITIVO": 0.8, "NEUTRO": 0.1, "NEGATIVO": 0.1}
    assert problema["NEGATIVO"] == 0.8
    assert neutro["NEUTRO"] == 0.8


def test_probabilidades_em_lote_trunca_antes_de_mandar_pro_modelo():
    classificador = FakeZeroShotClassifier()

    probabilidades_em_lote(classificador, ["x" * 5000])

    assert len(classificador.textos_recebidos[0]) == LIMITE_CARACTERES


def test_tom_do_post_usa_a_media_dos_pedacos():
    pedacos = [
        {"POSITIVO": 0.8, "NEUTRO": 0.1, "NEGATIVO": 0.1},
        {"POSITIVO": 0.2, "NEUTRO": 0.7, "NEGATIVO": 0.1},
    ]

    tom, score = tom_do_post(pedacos)

    assert tom == "POSITIVO"  # média 0.5 vs NEUTRO 0.4
    assert score == pytest.approx(0.4)  # 0.5 - 0.1


def test_tom_do_post_pedacos_neutros_puxam_o_score_para_zero():
    pedacos = [{"POSITIVO": 0.1, "NEUTRO": 0.8, "NEGATIVO": 0.1}] * 3

    tom, score = tom_do_post(pedacos)

    assert tom == "NEUTRO"
    assert score == pytest.approx(0.0)


def test_tom_do_post_sem_pedacos_explica_o_erro():
    with pytest.raises(ValueError, match="ao menos 1 dict"):
        tom_do_post([])
