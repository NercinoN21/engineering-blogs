"""Coletor do Uber Engineering (https://www.uber.com/blog/engineering/).

Técnica: Selenium (para paginar a listagem) + requests/BeautifulSoup
(para o conteúdo de cada post).

Por que Selenium aqui: testado manualmente com curl/requests puro, a
página de listagem devolve HTML quase vazio (nenhum link de post) porque
o conteúdo é montado inteiramente em React no navegador. Com Selenium,
depois de renderizar, aparecem tanto os posts quanto um botão "next" que
aponta para /us/en/blog/engineering/page/2/, page/3/, etc. — paginação
clássica, só que escondida atrás de JavaScript.

A listagem também mistura links de post com links de categorias do blog
da Uber em geral (advertising, earn, ride, eat, business...) — por isso
filtramos explicitamente essas categorias conhecidas.

Já a página de cada post é renderizada no servidor (prova: o texto do
artigo aparece em uma <div data-testid="content"> mesmo via curl puro),
então para o conteúdo usamos requests simples, sem precisar do navegador.
"""

import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

from .. import config
from ..database import upsert_post
from ..utils import clean_text, find_extenso_date, get_session, make_driver, polite_get

NOME_EMPRESA = "Uber"
BASE_URL = "https://www.uber.com/us/en/blog/engineering/"
MAX_PAGINAS = 60  # trava de segurança

CATEGORIAS_NAO_POST = {
    "engineering", "advertising", "earn", "ride", "eat", "merchants",
    "business", "health", "higher-education", "transit",
    "community-support", "freight",
}


def _eh_link_de_post(href: str) -> bool:
    m = re.match(r"^https://www\.uber\.com/us/en/blog/([a-z0-9-]+)/?$", href)
    if not m:
        return False
    return m.group(1) not in CATEGORIAS_NAO_POST


def _coletar_links_com_selenium(cutoff_date) -> list[str]:
    driver = make_driver()
    links_vistos: set[str] = set()
    try:
        for num_pagina in range(1, MAX_PAGINAS + 1):
            url_pagina = BASE_URL if num_pagina == 1 else f"{BASE_URL}page/{num_pagina}/"
            driver.get(url_pagina)
            time.sleep(config.SELENIUM_PAGE_LOAD_SLEEP)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            links_da_pagina = {
                a["href"] for a in soup.find_all("a", href=True) if _eh_link_de_post(a["href"])
            }
            if not links_da_pagina:
                break  # página vazia: acabou a listagem

            links_vistos.update(links_da_pagina)

            tem_proxima = soup.find(
                "a", string=lambda s: s and s.strip().lower() == "next"
            )
            if not tem_proxima:
                break
    finally:
        driver.quit()
    return sorted(links_vistos)


def _extrair_post(session, url: str) -> dict | None:
    resp = polite_get(session, url)
    if resp is None:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")

    titulo_tag = soup.find("meta", property="og:title")
    titulo = titulo_tag["content"].strip() if titulo_tag else soup.title.get_text(strip=True)

    data_pub = find_extenso_date(resp.text)
    if data_pub is None:
        return None

    corpo = soup.find(attrs={"data-testid": "content"})
    conteudo = clean_text(corpo) if corpo else ""
    if len(conteudo) < 150:
        # Ou é uma página de teste/placeholder que vazou pro sitemap (ex.:
        # /blog/1033latime/, título "Test"), ou um post usando um template
        # diferente do padrão (ex.: layout "newsroom"), onde o seletor
        # data-testid="content" não existe. Nos dois casos, melhor não
        # salvar um registro quase vazio do que inventar conteúdo.
        return None

    return {
        "empresa": NOME_EMPRESA,
        "titulo": titulo,
        "url": url,
        "data_publicacao": data_pub.isoformat(),
        "conteudo": conteudo,
        "janela_amostral": "5_anos",
    }


def collect(db, cutoff_date=config.CUTOFF_DATE) -> int:
    print(f"[{NOME_EMPRESA}] paginando listagem com Selenium...")
    links = _coletar_links_com_selenium(cutoff_date)
    print(f"[{NOME_EMPRESA}] {len(links)} URLs de posts encontradas.")

    session = get_session()
    salvos = 0
    for i, url in enumerate(links, 1):
        post = _extrair_post(session, url)
        if post is None:
            continue
        if post["data_publicacao"] < cutoff_date.isoformat():
            continue
        if upsert_post(db, post):
            salvos += 1
        if i % 20 == 0:
            print(f"[{NOME_EMPRESA}] {i}/{len(links)} verificados, {salvos} salvos até agora...")

    print(f"[{NOME_EMPRESA}] concluído: {salvos} posts salvos.")
    return salvos
