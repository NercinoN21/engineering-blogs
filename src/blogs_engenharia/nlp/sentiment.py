"""Classificação de sentimento dos posts (etapa 2): estima se o tom de
cada post é positivo ou negativo — um sinal que a contagem de palavras
da etapa 1 não captura (saber QUE palavras aparecem não diz COM QUE TOM
elas são usadas).

Modelo: `distilbert-base-uncased-finetuned-sst-2-english` — o modelo
padrão do pipeline `sentiment-analysis` da biblioteca transformers,
treinado em resenhas de filme (SST-2). Não é especializado em texto
técnico de engenharia, mas serve como primeira aproximação concreta do
tom — a mesma postura da etapa 1 ao usar Jaccard em vez de uma métrica
mais sofisticada.
"""

MODELO_SENTIMENTO = "distilbert-base-uncased-finetuned-sst-2-english"
LIMITE_CARACTERES = 2_000  # ~512 tokens, o máximo que o modelo aceita de uma vez
TAMANHO_LOTE = 32


def carregar_classificador_sentimento():
    """Carrega o pipeline de sentiment-analysis (baixado na 1ª execução).

    Import adiado pra dentro da função — ver motivo em
    `nlp/embeddings.py::carregar_modelo_embeddings`.
    """
    from transformers import pipeline

    return pipeline("sentiment-analysis", model=MODELO_SENTIMENTO, truncation=True)


def pontuar_sentimento_em_lote(classificador, textos: list[str]) -> list[float]:
    """Score com sinal de cada texto: +confiança se POSITIVE, −confiança se NEGATIVE.

    `classificador` é injetável em vez de criado aqui dentro (mesma
    razão de `embeddings.py::gerar_embeddings`): nos testes, um fake
    sem modelo real (ver `tests/fakes.py::FakeSentimentClassifier`).
    Trunca em `LIMITE_CARACTERES` antes de mandar pro modelo porque o
    pipeline do Hugging Face corta em tokens, não em caracteres — cortar
    antes evita mandar texto gigante e deixar o tokenizer truncar menos
    previsivelmente. Uma chamada só, em lote, é bem mais rápida que uma
    chamada por texto.
    Exemplo:
        pontuar_sentimento_em_lote(classificador, ["Great!", "Outage."])  # -> [0.99, -0.97]
    """
    resultados = classificador([t[:LIMITE_CARACTERES] for t in textos], batch_size=TAMANHO_LOTE)
    return [r["score"] if r["label"] == "POSITIVE" else -r["score"] for r in resultados]


def rotulo_do_score(score: float) -> tuple[str, float]:
    """Converte um score com sinal de volta em (rótulo, confiança).

    Mantém o formato que `semantic.py::sentimento_medio_por_empresa_ano`
    espera, o mesmo que o pipeline devolve para um texto.
    Exemplo:
        rotulo_do_score(-0.97)  # -> ("NEGATIVE", 0.97)
    """
    return ("POSITIVE" if score >= 0 else "NEGATIVE"), abs(score)
