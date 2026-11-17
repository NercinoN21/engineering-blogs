"""Classificação do tom dos posts (etapa 2): conquista, explicação neutra
ou problema — um sinal que a contagem de palavras da etapa 1 não captura
(saber QUE palavras aparecem não diz COM QUE TOM elas são usadas).

Modelo: `MoritzLaurer/deberta-v3-base-zeroshot-v2.0`, classificação
*zero-shot*: o modelo não foi treinado com estes rótulos; ele julga se o
texto confirma cada frase de `ROTULOS` (inferência textual, NLI). Isso
permite um rótulo NEUTRO, que faz falta em texto técnico.

Substitui o `distilbert-base-uncased-finetuned-sst-2-english` (modelo
padrão do pipeline `sentiment-analysis`, treinado em resenhas de filme).
Num gabarito de 79 posts rotulados à mão, o SST-2 acertou 29% — sem
classe neutra, errava todos os posts neutros, que são 59% da amostra; o
zero-shot lendo o post inteiro em pedaços acertou 72% (ver README,
"Modelo de sentimento").
"""

import numpy as np

MODELO_SENTIMENTO = "MoritzLaurer/deberta-v3-base-zeroshot-v2.0"
HIPOTESE = "This text {}."
ROTULOS = {
    "describes an achievement or improvement": "POSITIVO",
    "neutrally explains a technical topic": "NEUTRO",
    "describes a problem, failure or incident": "NEGATIVO",
}
LIMITE_CARACTERES = 2_000  # folga: um pedaço de 150 palavras tem ~1.000 caracteres
TAMANHO_LOTE = 16


def carregar_classificador_sentimento():
    """Carrega o pipeline de zero-shot-classification (baixado na 1ª execução).

    Import adiado pra dentro da função — ver motivo em
    `nlp/embeddings.py::carregar_modelo_embeddings`.
    """
    from transformers import pipeline

    return pipeline("zero-shot-classification", model=MODELO_SENTIMENTO, device=escolher_dispositivo())


def escolher_dispositivo() -> str:
    """GPU quando houver: no Mac (MPS), o DeBERTa roda ~9x mais rápido que na CPU.

    Exemplo:
        escolher_dispositivo()  # -> "mps", "cuda" ou "cpu"
    """
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def probabilidades_em_lote(classificador, textos: list[str]) -> list[dict[str, float]]:
    """Probabilidade de cada tom (POSITIVO/NEUTRO/NEGATIVO) para cada texto.

    `classificador` é injetável em vez de criado aqui dentro (mesma
    razão de `embeddings.py::gerar_embeddings`): nos testes, um fake
    sem modelo real (ver `tests/fakes.py::FakeZeroShotClassifier`).
    Uma chamada só, em lote, é bem mais rápida que uma chamada por texto.
    Exemplo:
        probabilidades_em_lote(clf, ["We cut costs by 94%."])
        # -> [{"POSITIVO": 0.9, "NEUTRO": 0.08, "NEGATIVO": 0.02}]
    """
    saidas = classificador(
        [t[:LIMITE_CARACTERES] for t in textos],
        candidate_labels=list(ROTULOS),
        hypothesis_template=HIPOTESE,
        batch_size=TAMANHO_LOTE,
    )
    return [{ROTULOS[r]: s for r, s in zip(saida["labels"], saida["scores"])} for saida in saidas]


def tom_do_post(probabilidades_dos_pedacos: list[dict[str, float]]) -> tuple[str, float]:
    """Combina os pedaços de um post em (tom predominante, score de −1 a +1).

    Tira a média das probabilidades dos pedaços: o tom é a classe com
    maior média, e o score é P(POSITIVO) − P(NEGATIVO) — pedaços neutros
    puxam o score para perto de zero em vez de forçar um lado.
    Exemplo:
        tom_do_post([{"POSITIVO": 0.8, "NEUTRO": 0.1, "NEGATIVO": 0.1}])  # -> ("POSITIVO", 0.7)
    """
    if not probabilidades_dos_pedacos:
        raise ValueError(f"post sem pedaços: esperava ao menos 1 dict de probabilidades, recebi {probabilidades_dos_pedacos!r}")
    media = {tom: float(np.mean([p[tom] for p in probabilidades_dos_pedacos])) for tom in ROTULOS.values()}
    return max(media, key=media.get), media["POSITIVO"] - media["NEGATIVO"]
