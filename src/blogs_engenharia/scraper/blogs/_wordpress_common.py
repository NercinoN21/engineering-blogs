"""Lógica compartilhada por todos os blogs que rodam em WordPress e
expõem a API REST nativa (`/wp-json/wp/v2/posts`): Slack, Meta,
Microsoft (ISE) e GitHub Engineering.

Essa API é a melhor fonte possível pra esse tipo de projeto: os campos
já vêm estruturados (sem precisar adivinhar seletor CSS), dá pra filtrar
por categoria e pra paginar sem depender de JavaScript. Confirmado
manualmente com curl, em cada um dos 4 sites, antes de escrever este
código, que o endpoint responde com `X-WP-Total` (quantos posts existem
no total) e um link `rel="next"` de paginação.

A API devolve os posts em ordem decrescente de data (mais novo primeiro)
por padrão, então paramos de paginar assim que achamos um post mais
antigo que a janela de corte.
"""

from datetime import date

import requests

from ..database import upsert_post
from ..utils import get_session, html_to_clean_text, polite_get

POR_PAGINA = 20


def collect_from_wp_rest_api(
    db,
    nome_empresa: str,
    api_url: str,
    cutoff_date: date,
    extra_params: dict | None = None,
    session: requests.Session | None = None,
) -> int:
    """Pagina a API REST do WordPress de `api_url` e salva os posts no `db`.

    `session` é injetável em vez de criado aqui dentro: em produção cada
    coletor chama sem passar nada (cai no `get_session()` real), e os
    testes passam uma sessão falsa para exercitar paginação/filtragem
    sem rede (ver `tests/test_wordpress_common.py`).
    """
    print(f"[{nome_empresa}] coletando via WordPress REST API ({api_url})...")
    session = session or get_session()

    salvos = 0
    pagina = 1
    while True:
        params = {"per_page": POR_PAGINA, "page": pagina, "orderby": "date", "order": "desc"}
        params.update(extra_params or {})
        resp = polite_get(session, api_url, params=params)
        if resp is None:
            break  # inclui o caso de page > total (API devolve 400)

        posts = resp.json()
        if not posts:
            break

        salvos, parou_na_janela = _salvar_pagina(db, nome_empresa, posts, cutoff_date, salvos)
        print(f"[{nome_empresa}] página {pagina} processada, {salvos} salvos até agora...")

        if parou_na_janela:
            break
        pagina += 1

    print(f"[{nome_empresa}] concluído: {salvos} posts salvos.")
    return salvos


def _salvar_pagina(
    db, nome_empresa: str, posts: list[dict], cutoff_date: date, salvos: int
) -> tuple[int, bool]:
    """Salva os posts de uma página que ainda estão dentro da janela de corte.

    Devolve (novo total de salvos, True se a página já cruzou a janela de
    corte e a paginação deve parar) — a API devolve os posts do mais novo
    pro mais antigo, então um post fora da janela encerra a busca.
    """
    for item in posts:
        data_pub = date.fromisoformat(item["date"][:10])
        if data_pub < cutoff_date:
            return salvos, True

        conteudo = html_to_clean_text(item["content"]["rendered"])
        if len(conteudo) < 150:
            # Alguns posts (visto no Meta: sustainability.atmeta.com,
            # metacareers.com, ai.meta.com...) existem no WordPress só
            # como um "ponteiro" — o artigo de verdade mora em outro
            # domínio da empresa, e o campo content.rendered vem vazio.
            # Melhor pular do que salvar um registro quase em branco.
            continue

        post = {
            "empresa": nome_empresa,
            "titulo": html_to_clean_text(item["title"]["rendered"]),
            "url": item["link"],
            "data_publicacao": data_pub.isoformat(),
            "conteudo": conteudo,
            "janela_amostral": "5_anos",
        }
        if upsert_post(db, post):
            salvos += 1
    return salvos, False
