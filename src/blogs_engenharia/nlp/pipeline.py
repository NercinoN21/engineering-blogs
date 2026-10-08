"""Análise linguística dos posts com spaCy.

Pra cada post, extraímos dois sinais:
  1. **Lemas relevantes**: substantivos e substantivos próprios (POS
     NOUN/PROPN), sem stopword/pontuação, lematizados (ex.: "scaling" e
     "scaled" viram "scale") — é a base pra contar "de que assunto esse
     post fala" sem contar "scaling" e "scale" como palavras diferentes.
  2. **Entidades nomeadas (NER)**: organizações, produtos, linguagens —
     um sinal a mais, complementar às siglas extraídas por regex em
     `preprocess.py`.

O componente `parser` do pipeline é desligado (`disable=["parser"]`):
ele é o mais caro computacionalmente e não usamos análise de
dependência sintática em nada deste projeto — só tagging (POS),
lematização e NER, que continuam funcionando sem o parser.
"""

import spacy

from .preprocess import extrair_siglas, limpar_para_nlp

MODELO = "en_core_web_sm"
TAMANHO_LOTE = 32

# Tipos de entidade do spaCy que interessam pro tema (organização,
# produto, linguagem/tecnologia nomeada). Os outros tipos (DATE, MONEY,
# CARDINAL...) não dizem nada sobre "assunto" do post.
TIPOS_DE_ENTIDADE_RELEVANTES = {"ORG", "PRODUCT", "LANGUAGE"}

STOPWORDS_EXTRAS = {
    "post", "blog", "team", "company", "today", "year", "way", "thing",
    "lot", "part", "time", "engineer", "engineering",  # aparecem em TODO post de TODO blog
    "figure", "table", "example",  # legendas de gráfico/imagem ("Figure 1"), não assunto do texto
}


def carregar_modelo():
    return spacy.load(MODELO, disable=["parser"])


# O lematizador do spaCy segue a regra "data é plural de datum", o que
# faz sentido em latim clássico mas não em texto de engenharia moderno
# (ninguém fala "um datum"). Corrigimos esse e outros poucos casos assim.
_CORRECOES_DE_LEMA = {"datum": "data", "medium": "media"}

# Comprimento mínimo 2 (não 3) de propósito: boa parte do jargão de
# tecnologia é sigla curta e carrega bastante significado (ai, ml, ci,
# cd, qa, ux, db...) — um corte em 3 letras jogaria tudo isso fora.
_TAMANHO_MINIMO_LEMA = 2


def _lemas_relevantes(doc) -> list[str]:
    lemas = []
    for token in doc:
        if token.pos_ not in ("NOUN", "PROPN"):
            continue
        if token.is_stop or token.is_punct or token.is_space:
            continue
        lema = token.lemma_.lower().strip()
        lema = _CORRECOES_DE_LEMA.get(lema, lema)
        if len(lema) < _TAMANHO_MINIMO_LEMA or not lema.isalpha():
            continue
        if lema in STOPWORDS_EXTRAS:
            continue
        lemas.append(lema)
    return lemas


def processar_posts(posts: list[dict], nlp=None, progresso_a_cada: int = 100):
    """Roda o pipeline em uma lista de posts (dicts vindos do TinyDB).

    Devolve um gerador de dicts: cada um tem os campos originais do post
    (empresa, url, data_publicacao) mais os sinais extraídos (lemas,
    entidades, siglas). Usa `nlp.pipe` (processamento em lote) em vez de
    chamar `nlp()` post a post — bem mais rápido no spaCy.
    """
    nlp = nlp or carregar_modelo()
    textos_limpos = [limpar_para_nlp(p["conteudo"]) for p in posts]

    for i, (post, doc) in enumerate(zip(posts, nlp.pipe(textos_limpos, batch_size=TAMANHO_LOTE)), 1):
        entidades = [e.text.strip() for e in doc.ents if e.label_ in TIPOS_DE_ENTIDADE_RELEVANTES]
        yield {
            "empresa": post["empresa"],
            "url": post["url"],
            "data_publicacao": post["data_publicacao"],
            "ano": post["data_publicacao"][:4],
            "lemas": _lemas_relevantes(doc),
            "entidades": entidades,
            "siglas": list(extrair_siglas(post["conteudo"]).elements()),
        }
        if progresso_a_cada and i % progresso_a_cada == 0:
            print(f"  [spaCy] {i}/{len(posts)} posts processados...")
