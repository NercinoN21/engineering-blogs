"""Coletor do Slack Engineering (https://slack.engineering).

Ver a explicação da técnica (API REST do WordPress) em
`_wordpress_common.py`. Confirmado manualmente: 194 posts no total.
"""

from .. import config
from ._wordpress_common import collect_from_wp_rest_api

NOME_EMPRESA = "Slack"
API_URL = "https://slack.engineering/wp-json/wp/v2/posts"


def collect(db, cutoff_date=config.CUTOFF_DATE) -> int:
    return collect_from_wp_rest_api(db, NOME_EMPRESA, API_URL, cutoff_date)
