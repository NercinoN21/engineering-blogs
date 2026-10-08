"""Coletor do Shopify Engineering (https://shopify.engineering).

Técnica: feed Atom (`feedparser`) para descobrir título, data e URL de
cada post, + requests/BeautifulSoup para o conteúdo completo.

Diferente do Medium (Netflix/Airbnb), o feed Atom da Shopify não é
paginado nem limitado aos itens mais recentes: uma única requisição a
`shopify.engineering/blog.atom` devolve os 432 posts do blog inteiro,
de 2010 até hoje (confirmado manualmente). Isso elimina o problema que
tivemos com Netflix/Airbnb — não existe limite de "só os 10 mais
recentes" aqui.

A diferença é que o Atom da Shopify só traz um resumo curto
(`summary`), não o post inteiro — por isso ainda precisamos visitar a
página de cada post para pegar o conteúdo completo (a página é
renderizada no servidor, texto dentro de uma tag <article> comum).
Como o feed já dá a data de cada post, filtramos pela janela de 5 anos
*antes* de visitar qualquer página, evitando requisições desnecessárias
(mesma otimização aplicada ao sitemap do Dropbox).
"""

from datetime import date

import feedparser
from bs4 import BeautifulSoup

from .. import config
from ..database import upsert_post
from ..utils import clean_text, get_session, polite_get

NOME_EMPRESA = "Shopify"
FEED_URL = "https://shopify.engineering/blog.atom"


def _extrair_conteudo(session, url: str) -> str:
    resp = polite_get(session, url)
    if resp is None:
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    artigo = soup.find("article")
    return clean_text(artigo) if artigo else ""


def collect(db, cutoff_date=config.CUTOFF_DATE) -> int:
    print(f"[{NOME_EMPRESA}] lendo feed Atom ({FEED_URL})...")
    feed = feedparser.parse(FEED_URL)
    print(f"[{NOME_EMPRESA}] {len(feed.entries)} posts no feed (histórico completo).")

    candidatos = [
        e for e in feed.entries
        if getattr(e, "published_parsed", None) and date(*e.published_parsed[:3]) >= cutoff_date
    ]
    print(f"[{NOME_EMPRESA}] {len(candidatos)} dentro da janela de {config.JANELA_EM_ANOS} anos.")

    session = get_session()
    salvos = 0
    for i, entry in enumerate(candidatos, 1):
        conteudo = _extrair_conteudo(session, entry.link)
        if len(conteudo) < 150:
            continue  # extração falhou (template diferente, página removida etc.)

        post = {
            "empresa": NOME_EMPRESA,
            "titulo": entry.title,
            "url": entry.link,
            "data_publicacao": date(*entry.published_parsed[:3]).isoformat(),
            "conteudo": conteudo,
            "janela_amostral": "5_anos",
        }
        if upsert_post(db, post):
            salvos += 1
        if i % 20 == 0:
            print(f"[{NOME_EMPRESA}] {i}/{len(candidatos)} verificados, {salvos} salvos até agora...")

    print(f"[{NOME_EMPRESA}] concluído: {salvos} posts salvos.")
    return salvos
