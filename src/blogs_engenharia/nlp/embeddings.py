"""Embeddings semânticos dos posts (etapa 2): representa cada resumo de
post como um vetor, permitindo comparar empresas por SIGNIFICADO em vez
de só por palavra exata (como a similaridade de Jaccard da etapa 1).

Modelo: `all-MiniLM-L6-v2` (sentence-transformers) — ~90MB, rápido o
bastante pra rodar em CPU sobre ~1.150 posts em poucos minutos, e é o
modelo mais usado em tutoriais de similaridade semântica (bom ponto de
partida pra quem está vendo isso pela primeira vez).
"""

MODELO_EMBEDDINGS = "all-MiniLM-L6-v2"


def carregar_modelo_embeddings():
    """Carrega o modelo de sentence-transformers (baixado na 1ª execução).

    Import adiado pra dentro da função: carregar o pacote inteiro (e o
    torch que ele arrasta) só quando alguém realmente pede o modelo,
    mesma ideia de `scraper/utils.py::make_driver` com o Selenium.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODELO_EMBEDDINGS)


def gerar_embeddings(modelo, textos: list[str]):
    """Converte uma lista de textos numa matriz de vetores (um por linha).

    `modelo` é injetável em vez de criado aqui dentro: em produção é o
    `SentenceTransformer` real; nos testes, um fake com `.encode()` que
    não baixa nada (ver `tests/fakes.py::FakeEmbeddingModel`).
    `normalize_embeddings=True` deixa os vetores com norma 1, o que
    simplifica a similaridade de cosseno depois (`nlp/semantic.py`).
    """
    return modelo.encode(textos, show_progress_bar=False, normalize_embeddings=True)
