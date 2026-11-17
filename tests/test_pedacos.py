from blogs_engenharia.nlp.pedacos import achatar, carregar_segmentador_de_frases, dividir_em_pedacos, reagrupar


def test_dividir_em_pedacos_agrupa_frases_ate_o_limite():
    segmentador = carregar_segmentador_de_frases()
    texto = "One two three. Four five six. Seven eight nine."

    pedacos = dividir_em_pedacos(segmentador, texto, max_palavras=6)

    assert pedacos == ["One two three. Four five six.", "Seven eight nine."]


def test_dividir_em_pedacos_texto_curto_vira_um_pedaco_so():
    segmentador = carregar_segmentador_de_frases()

    pedacos = dividir_em_pedacos(segmentador, "Short post.", max_palavras=150)

    assert pedacos == ["Short post."]


def test_dividir_em_pedacos_quebra_frase_maior_que_o_limite():
    segmentador = carregar_segmentador_de_frases()
    # Sem pontuação (tipo um bloco de código): uma "frase" de 10 palavras.
    texto = "a b c d e f g h i j"

    pedacos = dividir_em_pedacos(segmentador, texto, max_palavras=4)

    assert pedacos == ["a b c d", "e f g h", "i j"]
    assert all(len(p.split()) <= 4 for p in pedacos)


def test_achatar_guarda_quantos_pedacos_cada_post_tem():
    textos, tamanhos = achatar([["a", "b"], ["c"]])

    assert textos == ["a", "b", "c"]
    assert tamanhos == [2, 1]


def test_reagrupar_desfaz_achatar():
    textos, tamanhos = achatar([["a", "b"], ["c"], ["d", "e", "f"]])

    assert reagrupar(textos, tamanhos) == [["a", "b"], ["c"], ["d", "e", "f"]]
