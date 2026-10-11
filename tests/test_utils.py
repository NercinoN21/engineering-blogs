from datetime import date

from bs4 import BeautifulSoup

from blogs_engenharia.scraper.utils import clean_text, find_extenso_date, html_to_clean_text


def test_clean_text_achata_espacos_e_quebras_de_linha():
    soup = BeautifulSoup("<p>Olá   <b>mundo</b>\n\ncheio de    espaços</p>", "html.parser")

    assert clean_text(soup) == "Olá mundo cheio de espaços"


def test_html_to_clean_text_extrai_texto_visivel():
    html = "<article><h1>Título</h1><p>Corpo</p></article>"

    assert html_to_clean_text(html) == "Título Corpo"


def test_find_extenso_date_reconhece_data_por_extenso():
    html = "<div>Publicado em May 17, 2022 pelo time.</div>"

    assert find_extenso_date(html) == date(2022, 5, 17)


def test_find_extenso_date_devolve_none_quando_nao_acha_data():
    assert find_extenso_date("<div>sem data por extenso aqui</div>") is None
