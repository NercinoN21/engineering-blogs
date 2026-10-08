"""Camada de acesso ao TinyDB.

Guardamos todos os posts, de todos os blogs, em um único arquivo JSON
(`data/posts.json`), com um documento por post. O TinyDB funciona como
um "dicionário Python que persiste em disco": não precisa de servidor,
não precisa de schema, e dá pra ler o arquivo com qualquer editor de texto.
"""

from tinydb import Query, TinyDB

from . import config


def get_db() -> TinyDB:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return TinyDB(config.DB_PATH, indent=2, ensure_ascii=False)


def upsert_post(db: TinyDB, post: dict) -> bool:
    """Insere um post, evitando duplicata (chave natural = URL).

    Rodar o scraper de novo não deve duplicar posts já salvos — por isso
    usamos `upsert` (atualiza se a URL já existir, insere se for nova) em
    vez de `insert`. Isso também permite reexecutar o script depois de uma
    falha de rede no meio da coleta sem recomeçar do zero.

    Devolve True se o post era novo, False se já existia (e foi atualizado).
    """
    Post = Query()
    era_novo = db.count(Post.url == post["url"]) == 0
    db.upsert(post, Post.url == post["url"])
    return era_novo
