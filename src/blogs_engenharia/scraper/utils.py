"""Funções auxiliares usadas por todos os coletores (blogs/*.py)."""

import random
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from . import config

_MESES = (
    "January|February|March|April|May|June|July|August|"
    "September|October|November|December"
)
_PADRAO_DATA_EXTENSO = re.compile(rf"({_MESES})\s+\d{{1,2}},?\s+\d{{4}}")


def get_session() -> requests.Session:
    """Cria uma sessão requests com cabeçalhos de navegador real.

    Vários desses blogs (Uber, Dropbox, Spotify) devolvem HTTP 403/406
    para clientes sem um cabeçalho `User-Agent` e `Accept` parecido com
    o de um navegador — foi verificado manualmente com curl antes de
    escrever este scraper.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def polite_get(session: requests.Session, url: str, delay_range=None, **kwargs):
    """GET com pequena pausa aleatória antes da chamada (scraping educado).

    Retorna o Response em caso de sucesso (status 200 e corpo não-vazio)
    ou None em caso de erro — o chamador decide se quer pular o post ou
    abortar.

    Importante: alguns sites (ex.: dropbox.tech, atrás de AWS WAF) não
    devolvem um erro HTTP quando bloqueiam um robô — devolvem HTTP 202
    com corpo vazio e o cabeçalho `x-amzn-waf-action: challenge`. Se
    tratássemos isso como sucesso, o post seria salvo com conteúdo vazio
    (ou descartado silenciosamente por "não achar a data"), e pareceria
    que a empresa simplesmente não publicou mais nada — mascarando o
    bloqueio real. Por isso verificamos explicitamente corpo vazio/curto
    demais e avisamos no terminal.
    """
    time.sleep(random.uniform(*(delay_range or config.DELAY_RANGE)))
    try:
        resp = session.get(url, timeout=config.REQUEST_TIMEOUT, **kwargs)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"  [aviso] falha ao buscar {url}: {exc}")
        return None

    if resp.headers.get("x-amzn-waf-action") == "challenge":
        print(f"  [BLOQUEADO] WAF desafiou o robô em {url} — pare e espere antes de tentar de novo.")
        return None
    if len(resp.content) < 50:
        print(f"  [aviso] resposta vazia/curta demais em {url} (possível bloqueio silencioso)")
        return None
    return resp


def clean_text(node) -> str:
    """Extrai texto legível de um elemento BeautifulSoup (ou lista deles).

    Junta os textos com espaço, remove espaços duplicados e quebras de
    linha excessivas — o resultado é um parágrafo "achatado", melhor para
    salvar em um documento do TinyDB do que o texto bruto do HTML.
    """
    if isinstance(node, (list, tuple)):
        texto = " ".join(n.get_text(separator=" ", strip=True) for n in node)
    else:
        texto = node.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", texto).strip()


def html_to_clean_text(html: str) -> str:
    """Atalho: HTML bruto -> texto limpo, via BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    return clean_text(soup)


def find_extenso_date(html: str):
    """Procura uma data no formato 'Month D, YYYY' (ex.: 'May 17, 2022')
    dentro de um HTML e devolve um `datetime.date`, ou None se não achar.

    Usado nos blogs (Uber, Dropbox) que não expõem a data em uma tag
    <time> nem em meta tags — a data só aparece como texto visível.
    """
    m = _PADRAO_DATA_EXTENSO.search(html)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(0).replace(",", ""), "%B %d %Y").date()
    except ValueError:
        return None


def make_driver():
    """Cria um Chrome headless configurado para raspagem.

    Selenium 4.6+ baixa o chromedriver sozinho (Selenium Manager), então
    não é preciso instalar nada manualmente além do Google Chrome.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument(f"--window-size={config.SELENIUM_WINDOW_SIZE}")
    options.add_argument("--lang=en-US")
    options.add_argument(f"user-agent={config.USER_AGENT}")
    return webdriver.Chrome(options=options)
