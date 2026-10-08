"""Coletor do Meta Engineering (https://engineering.fb.com).

Ver a explicação da técnica (API REST do WordPress) em
`_wordpress_common.py`. Confirmado manualmente: 1.127 posts no total —
de longe o blog mais prolífico dos 7 coletados neste projeto.
"""

from .. import config
from ._wordpress_common import collect_from_wp_rest_api

NOME_EMPRESA = "Meta"
API_URL = "https://engineering.fb.com/wp-json/wp/v2/posts"


def collect(db, cutoff_date=config.CUTOFF_DATE) -> int:
    return collect_from_wp_rest_api(db, NOME_EMPRESA, API_URL, cutoff_date)
