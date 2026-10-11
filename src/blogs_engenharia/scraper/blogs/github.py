"""Coletor do GitHub Engineering (https://github.blog/engineering/).

`github.blog` publica muito mais do que engenharia (produto, comunidade,
changelog...) — 4.152 posts no total, sem filtro. Por isso filtramos
pela categoria "Engineering" (id 72 na API, confirmado manualmente via
`/wp-json/wp/v2/categories?search=engineering`), que sozinha tem 175
posts.

Ver a explicação da técnica (API REST do WordPress) em
`_wordpress_common.py`.
"""

import requests

from .. import config
from ._wordpress_common import collect_from_wp_rest_api

NOME_EMPRESA = "GitHub"
API_URL = "https://github.blog/wp-json/wp/v2/posts"
CATEGORIA_ENGINEERING = 72


def collect(db, cutoff_date=config.CUTOFF_DATE, session: requests.Session | None = None) -> int:
    return collect_from_wp_rest_api(
        db,
        NOME_EMPRESA,
        API_URL,
        cutoff_date,
        extra_params={"categories": CATEGORIA_ENGINEERING},
        session=session,
    )
