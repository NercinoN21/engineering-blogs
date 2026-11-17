"""Divide o post inteiro em pedaços que cabem no modelo de embeddings (etapa 2).

Substitui o resumo das 3 primeiras frases (`nlp/resumo.py`) como
entrada dos embeddings: em vez de olhar só a introdução, cada post é
lido por inteiro, em pedaços de frases consecutivas. Cada pedaço vira
um embedding e o post é a média deles (ver
`embeddings.py::gerar_embeddings_por_post`). Na comparação, o vetor do
post passou a achar o próprio título entre os 1.157 em 68% dos casos,
contra 58% com o resumo (ver README, "Resumo vs. post inteiro").

O MiniLM lê no máximo 256 tokens e ignora o resto sem avisar. Texto
técnico em inglês dá ~1,3 token por palavra, então 150 palavras ficam
abaixo desse limite: medido com o tokenizador do modelo, a mediana é
180 tokens e só 3,5% dos pedaços passam de 256 (trechos de código).
"""

MAX_PALAVRAS_POR_PEDACO = 150


def dividir_em_pedacos(segmentador, texto: str, max_palavras: int = MAX_PALAVRAS_POR_PEDACO) -> list[str]:
    """Agrupa frases consecutivas em pedaços de até `max_palavras` palavras.

    Corta sempre entre frases, para nenhum pedaço começar no meio de uma.
    Exemplo:
        dividir_em_pedacos(segmentador, post["conteudo"])  # -> ["We built...", "Then..."]
    """
    pedacos: list[str] = []
    atual: list[str] = []
    palavras_no_atual = 0
    for frase in _frases_que_cabem(segmentador, texto, max_palavras):
        n_palavras = len(frase.split())
        if atual and palavras_no_atual + n_palavras > max_palavras:
            pedacos.append(" ".join(atual))
            atual, palavras_no_atual = [], 0
        atual.append(frase)
        palavras_no_atual += n_palavras
    if atual:
        pedacos.append(" ".join(atual))
    return pedacos


def _frases_que_cabem(segmentador, texto: str, max_palavras: int) -> list[str]:
    """Frases do texto, quebrando em janelas as que sozinhas passam do limite.

    Trechos de código ou listas sem pontuação viram uma "frase" gigante
    para o sentencizer — sem essa quebra, estourariam o limite do modelo.
    """
    frases: list[str] = []
    for sent in segmentador(texto).sents:
        palavras = sent.text.split()
        for inicio in range(0, len(palavras), max_palavras):
            frases.append(" ".join(palavras[inicio : inicio + max_palavras]))
    return frases


def achatar(pedacos_por_post: list[list[str]]) -> tuple[list[str], list[int]]:
    """Junta os pedaços de todos os posts numa lista só, guardando quantos são de cada post.

    Os modelos rodam bem mais rápido com uma chamada em lote do que com
    uma chamada por post; `reagrupar` desfaz a junção depois.
    Exemplo:
        achatar([["a", "b"], ["c"]])  # -> (["a", "b", "c"], [2, 1])
    """
    textos = [pedaco for pedacos in pedacos_por_post for pedaco in pedacos]
    return textos, [len(pedacos) for pedacos in pedacos_por_post]


def reagrupar(valores: list, tamanhos: list[int]) -> list[list]:
    """Inverso de `achatar`: separa os resultados de volta, post a post.

    Exemplo:
        reagrupar([1, 2, 3], [2, 1])  # -> [[1, 2], [3]]
    """
    grupos: list[list] = []
    inicio = 0
    for tamanho in tamanhos:
        grupos.append(list(valores[inicio : inicio + tamanho]))
        inicio += tamanho
    return grupos
