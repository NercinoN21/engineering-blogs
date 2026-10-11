from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from blogs_engenharia.scraper.database import upsert_post


def _db() -> TinyDB:
    return TinyDB(storage=MemoryStorage)


def test_upsert_post_insere_post_novo():
    db = _db()

    era_novo = upsert_post(db, {"url": "https://x/1", "titulo": "A"})

    assert era_novo is True
    assert len(db.all()) == 1


def test_upsert_post_atualiza_em_vez_de_duplicar():
    db = _db()
    upsert_post(db, {"url": "https://x/1", "titulo": "A"})

    era_novo = upsert_post(db, {"url": "https://x/1", "titulo": "B"})

    assert era_novo is False
    assert len(db.all()) == 1
    assert db.all()[0]["titulo"] == "B"
