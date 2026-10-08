"""Coletor do blog de engenharia da Microsoft.

A Microsoft não tem "um" blog de engenharia central como os outros —
`devblogs.microsoft.com` é, na verdade, dezenas de blogs separados
hospedados sob o mesmo domínio (`/dotnet`, `/typescript`,
`/oldnewthing`, `/powershell`...), cada um com seu próprio WordPress e
sua própria API REST. A maioria deles é focada em uma linguagem/produto
específico (changelog de release, por exemplo), bem diferente do
"como resolvemos esse problema de engenharia em escala" que é o padrão
dos outros 6 blogs deste projeto.

Dentre as opções, `devblogs.microsoft.com/ise` (**ISE = Industry
Solutions Engineering**, o time de engenharia que trabalha em projetos
de clientes da Microsoft) é o mais parecido em espírito com Uber/Meta/
Slack Engineering: posts de estudo de caso de problemas de engenharia
reais, não documentação de produto. Confirmado manualmente: 319 posts no
total.

Ver a explicação da técnica (API REST do WordPress) em
`_wordpress_common.py`.
"""

from .. import config
from ._wordpress_common import collect_from_wp_rest_api

NOME_EMPRESA = "Microsoft"
API_URL = "https://devblogs.microsoft.com/ise/wp-json/wp/v2/posts"


def collect(db, cutoff_date=config.CUTOFF_DATE) -> int:
    return collect_from_wp_rest_api(db, NOME_EMPRESA, API_URL, cutoff_date)
