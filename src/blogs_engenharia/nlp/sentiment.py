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


def carregar_classificador_sentimento():
    """Carrega o pipeline de sentiment-analysis (baixado na 1ª execução).

    Import adiado pra dentro da função — ver motivo em
    `nlp/embeddings.py::carregar_modelo_embeddings`.
    """
    from transformers import pipeline

    return pipeline("sentiment-analysis", model=MODELO_SENTIMENTO, truncation=True)


def classificar_sentimento(classificador, texto: str) -> tuple[str, float]:
    """Devolve (rótulo, confiança) do texto — rótulo é "POSITIVE" ou "NEGATIVE".

    `classificador` é injetável em vez de criado aqui dentro (mesma
    razão de `embeddings.py::gerar_embeddings`): nos testes, um fake
    sem modelo real (ver `tests/fakes.py::FakeSentimentClassifier`).
    Trunca em `LIMITE_CARACTERES` antes de mandar pro modelo porque o
    pipeline do Hugging Face corta em tokens, não em caracteres — cortar
    antes evita mandar texto gigante e deixar o tokenizer truncar menos
    previsivelmente.
    """
    resultado = classificador(texto[:LIMITE_CARACTERES])[0]
    return resultado["label"], resultado["score"]
