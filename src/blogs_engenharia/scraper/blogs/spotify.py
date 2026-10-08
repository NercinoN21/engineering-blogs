"""Coletor do Spotify Engineering (https://engineering.atspotify.com).

Técnica: Selenium (para descobrir os links dos posts) + requests/BeautifulSoup
(para baixar o conteúdo de cada post).

Por que Selenium aqui: a home do blog é uma aplicação Next.js que carrega
os posts via JavaScript e usa um botão "load more" (sem link de paginação
em URL) para trazer mais posts conforme o usuário clica. Testado
manualmente: com requests puro, 0 links de post aparecem no HTML; com
Selenium clicando em "load more" 6 vezes, aparecem 85 posts (de 2022 até
2026). Por isso é um caso legítimo de uso de navegador automatizado, e
não só de BeautifulSoup.

Já a página de cada post individual é renderizada no servidor (SSR), então
para o conteúdo usamos requests simples — não precisamos abrir um navegador
para cada post, só para a listagem. Isso economiza bastante tempo.
"""

import re
from datetime import datetime

from selenium.webdriver.common.by import By

from .. import config
from ..database import upsert_post
from ..utils import clean_text, get_session, make_driver, polite_get

NOME_EMPRESA = "Spotify"
HOME_URL = "https://engineering.atspotify.com/"
PADRAO_LINK_POST = re.compile(r"^(https://engineering\.atspotify\.com)?/\d{4}/\d{1,2}/[a-z0-9-]+/?$")
MAX_CLIQUES = 40  # trava de segurança para não rodar pra sempre


def _data_do_link(url: str):
    m = re.search(r"/(\d{4})/(\d{1,2})/", url)
    if not m:
        return None
    ano, mes = int(m.group(1)), int(m.group(2))
    return datetime(ano, mes, 1).date()


def _coletar_links_com_selenium(cutoff_date) -> list[str]:
    driver = make_driver()
    try:
        driver.get(HOME_URL)
        import time

        time.sleep(config.SELENIUM_PAGE_LOAD_SLEEP)

        for clique in range(MAX_CLIQUES):
            links = {
                a.get_attribute("href")
                for a in driver.find_elements(By.TAG_NAME, "a")
                if a.get_attribute("href") and PADRAO_LINK_POST.match(a.get_attribute("href"))
            }
            datas = [d for d in (_data_do_link(u) for u in links) if d]
            mais_antiga = min(datas) if datas else None
            if mais_antiga and mais_antiga < cutoff_date:
                break  # já cobrimos a janela de 5 anos, não precisa clicar mais
            try:
                botao = driver.find_element(
                    By.XPATH, "//button[contains(translate(text(),'LOAD MORE','load more'),'load more')]"
                )
                driver.execute_script("arguments[0].click();", botao)
                time.sleep(1.5)
            except Exception:
                break  # botão sumiu: chegamos ao fim da lista

        links = {
            a.get_attribute("href")
            for a in driver.find_elements(By.TAG_NAME, "a")
            if a.get_attribute("href") and PADRAO_LINK_POST.match(a.get_attribute("href"))
        }
        return sorted(links)
    finally:
        driver.quit()


def _extrair_post(session, url: str) -> dict | None:
    resp = polite_get(session, url)
    if resp is None:
        return None
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(resp.text, "html.parser")

    titulo_tag = soup.find("meta", property="og:title")
    titulo = titulo_tag["content"].split("|")[0].strip() if titulo_tag else soup.title.get_text(strip=True)

    data_div = soup.find("div", class_="date")
    data_pub = _data_do_link(url)
    if data_div:
        try:
            data_pub = datetime.strptime(data_div.get_text(strip=True), "%b %d, %Y").date()
        except ValueError:
            pass

    # A maioria dos posts usa a template "html-content". A série de
    # entrevistas curtas "My Beat" (perfis de funcionários) usa outra
    # template ("content-wrapper") — descoberto verificando manualmente
    # por que alguns posts ficavam com conteúdo vazio.
    corpo = soup.find("div", class_="html-content") or soup.find("div", class_="content-wrapper")
    conteudo = clean_text(corpo) if corpo else ""
    if len(conteudo) < 150:
        return None  # template desconhecido: melhor não salvar quase vazio

    return {
        "empresa": NOME_EMPRESA,
        "titulo": titulo,
        "url": url,
        "data_publicacao": data_pub.isoformat() if data_pub else None,
        "conteudo": conteudo,
        "janela_amostral": "5_anos",
    }


def collect(db, cutoff_date=config.CUTOFF_DATE) -> int:
    print(f"[{NOME_EMPRESA}] descobrindo posts com Selenium (clicando em 'load more')...")
    links = _coletar_links_com_selenium(cutoff_date)
    print(f"[{NOME_EMPRESA}] {len(links)} URLs de posts encontradas.")

    session = get_session()
    salvos = 0
    for i, url in enumerate(links, 1):
        post = _extrair_post(session, url)
        if post is None or post["data_publicacao"] is None:
            continue
        if post["data_publicacao"] < cutoff_date.isoformat():
            continue
        if upsert_post(db, post):
            salvos += 1
        if i % 20 == 0:
            print(f"[{NOME_EMPRESA}] {i}/{len(links)} verificados, {salvos} salvos até agora...")

    print(f"[{NOME_EMPRESA}] concluído: {salvos} posts salvos.")
    return salvos
