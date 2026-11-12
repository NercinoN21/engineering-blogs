from blogs_engenharia.nlp.resumo import carregar_segmentador_de_frases, extrair_resumo


def test_extrair_resumo_junta_as_primeiras_frases():
    segmentador = carregar_segmentador_de_frases()
    texto = "Primeira frase. Segunda frase. Terceira frase. Quarta frase, que não deve entrar."

    resumo = extrair_resumo(segmentador, texto, n_frases=3)

    assert resumo == "Primeira frase. Segunda frase. Terceira frase."


def test_extrair_resumo_com_menos_frases_que_o_limite():
    segmentador = carregar_segmentador_de_frases()
    texto = "Única frase do post."

    resumo = extrair_resumo(segmentador, texto, n_frases=3)

    assert resumo == "Única frase do post."
