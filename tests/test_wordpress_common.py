from datetime import date

from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from blogs_engenharia.scraper import utils as scraper_utils
from blogs_engenharia.scraper.blogs._wordpress_common import collect_from_wp_rest_api

from .fakes import FakeWordPressSession

CUTOFF = date(2024, 1, 1)


def _item(url: str, data: str, conteudo: str = "a" * 200) -> dict:
    return {
        "date": f"{data}T10:00:00",
        "link": url,
        "title": {"rendered": "Título"},
        "content": {"rendered": f"<p>{conteudo}</p>"},
    }


def _db() -> TinyDB:
    return TinyDB(storage=MemoryStorage)


def test_para_na_janela_de_corte_e_nao_salva_posts_mais_antigos(monkeypatch):
    monkeypatch.setattr(scraper_utils.config, "DELAY_RANGE", (0, 0))
    db = _db()
    session = FakeWordPressSession(paginas=[
        [_item("https://x/1", "2026-01-10"), _item("https://x/2", "2020-01-10")],
    ])

    salvos = collect_from_wp_rest_api(db, "Meta", "https://x/wp-json/wp/v2/posts", CUTOFF, session=session)

    assert salvos == 1
    assert db.all()[0]["url"] == "https://x/1"


def test_pula_post_ponteiro_com_conteudo_curto_demais(monkeypatch):
    monkeypatch.setattr(scraper_utils.config, "DELAY_RANGE", (0, 0))
    db = _db()
    session = FakeWordPressSession(paginas=[
        [_item("https://x/1", "2026-01-10", conteudo="curto"), _item("https://x/2", "2026-01-11")],
    ])

    salvos = collect_from_wp_rest_api(db, "Meta", "https://x/wp-json/wp/v2/posts", CUTOFF, session=session)

    assert salvos == 1
    assert db.all()[0]["url"] == "https://x/2"


def test_upsert_evita_duplicata_entre_execucoes(monkeypatch):
    monkeypatch.setattr(scraper_utils.config, "DELAY_RANGE", (0, 0))
    db = _db()
    item = _item("https://x/1", "2026-01-10")

    collect_from_wp_rest_api(db, "Meta", "https://x", CUTOFF, session=FakeWordPressSession(paginas=[[item]]))
    salvos_segunda_vez = collect_from_wp_rest_api(
        db, "Meta", "https://x", CUTOFF, session=FakeWordPressSession(paginas=[[item]])
    )

    assert len(db.all()) == 1
    assert salvos_segunda_vez == 0
