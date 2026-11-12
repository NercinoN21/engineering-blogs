"""Extrai um resumo curto de cada post (etapa 2): as primeiras frases,
usadas como entrada pros modelos de embedding e sentimento.

Usa um pipeline spaCy *em branco* (`spacy.blank`) com só o componente
`sentencizer` — diferente do pipeline da etapa 1 (`en_core_web_sm`, com
tagger/lematizador/NER), aqui só precisamos separar frases, e o
sentencizer baseado em regras é ordens de magnitude mais rápido que
carregar o modelo estatístico inteiro só pra essa tarefa. Mandar o post
inteiro pros modelos de embedding/sentimento seria lento à toa: o
começo de um post técnico já concentra o assunto e o tom principal
(mesma lógica do truncamento em `preprocess.py::limpar_para_nlp`).
"""

import spacy


def carregar_segmentador_de_frases():
    """Pipeline spaCy só com separação de frases (sem modelo estatístico)."""
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp


def extrair_resumo(segmentador, texto: str, n_frases: int = 3) -> str:
    """Junta as primeiras `n_frases` do texto, como resumo do post.

    `segmentador` é injetável (ver `carregar_segmentador_de_frases`),
    permitindo reaproveitar o mesmo pipeline entre chamadas e, nos
    testes, usar um pipeline em branco de verdade sem nenhum mock —
    o sentencizer não baixa nada, então o teste continua rápido.
    """
    doc = segmentador(texto)
    frases = [sent.text.strip() for sent in doc.sents][:n_frases]
    return " ".join(frases)
