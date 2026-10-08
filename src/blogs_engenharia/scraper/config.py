"""Configurações compartilhadas por todos os coletores do projeto.

Tema: Convergência e divergência temática entre blogs de engenharia
de grandes empresas de tecnologia ao longo do tempo (UFPB - Modelagem
de Dados Não Estruturados).
"""

from datetime import date, timedelta
from pathlib import Path

# --- Janela temporal da amostra -------------------------------------------
# Decisão: últimos 5 anos a partir da data de execução. Ver justificativa
# no README.md e em explicando_para_uma_crianca_de_10_anos.md. Resumo:
# 5 anos é o período em que TODOS os 6 blogs escolhidos já existiam e
# publicavam com regularidade, o que torna a amostra comparável entre
# empresas (evita viés de "empresa mais antiga = mais posts").
JANELA_EM_ANOS = 5
CUTOFF_DATE = date.today() - timedelta(days=365 * JANELA_EM_ANOS)

# --- Caminhos ---------------------------------------------------------------
# parents[3]: scraper/ -> blogs_engenharia/ -> src/ -> raiz do projeto.
# É nessa raiz que mora data/posts.json, fora do pacote instalável.
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "posts.json"

# --- HTTP ---------------------------------------------------------------
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 "
    "(projeto-academico-UFPB-modelagem-dados-nao-estruturados)"
)
REQUEST_TIMEOUT = 20  # segundos
# Intervalo (mínimo, máximo) de espera entre requisições, em segundos.
# Scraping "educado": evita martelar os servidores dos blogs.
DELAY_RANGE = (0.6, 1.4)

# --- Selenium ---------------------------------------------------------------
SELENIUM_WINDOW_SIZE = "1400,2400"
SELENIUM_PAGE_LOAD_SLEEP = 2.5  # espera após cada ação para o JS renderizar
