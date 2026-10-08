"""Agrega os sinais extraídos pelo spaCy (um por post) em estatísticas
por empresa e por ano, e calcula as métricas que respondem a pergunta do
projeto: os blogs convergem ou divergem ao longo do tempo?

Duas análises, cada uma olhando pra uma metade da pergunta:

1. **Matriz de convergência** (`matriz_convergencia`): o quanto os
   termos mais usados por cada empresa se sobrepõem aos de outra, no
   período inteiro (últimos 5 anos). Responde "quem fala de assuntos
   parecidos" — a dimensão *entre empresas*.
2. **Evolução de termos "quentes"** (`evolucao_termos`): a frequência de
   um punhado de termos de interesse (ex.: "ai", "kubernetes") por
   empresa, ano a ano. Responde "quando cada empresa começou a falar
   disso" — a dimensão *ao longo do tempo*.

Uma matriz de convergência ano a ano (em vez de só uma, pro período
inteiro) foi descartada de propósito: com só ~10-20 posts de algumas
empresas em alguns anos, o conjunto de "termos mais frequentes" fica
pequeno e instável demais pra comparar com confiança — a dimensão
temporal fica melhor representada pelos termos quentes, que são uma
contagem simples (soma), não um "top-N" ruidoso.
"""

from collections import Counter, defaultdict

TERMOS_QUENTES = [
    "ai", "llm", "ml", "kubernetes", "security", "cloud", "api",
    "performance", "data", "latency", "testing", "migration",
]

# Cada empresa cita o próprio nome o tempo todo ("no blog da Uber falamos
# sobre como a Uber fez X") — é o termo nº1 em todo mundo e não diz nada
# sobre *assunto*, só sobre quem é o autor. Removido antes de agregar.
_AUTORREFERENCIA = {
    "GitHub": {"github"}, "Meta": {"meta"}, "Microsoft": {"microsoft"},
    "Shopify": {"shopify"}, "Slack": {"slack"}, "Spotify": {"spotify"},
    "Uber": {"uber"},
}


def _lemas_sem_autorreferencia(empresa: str, lemas: list[str]) -> list[str]:
    ignorar = _AUTORREFERENCIA.get(empresa, set())
    return [l for l in lemas if l not in ignorar]


def agregar_por_empresa(registros: list[dict]) -> dict[str, Counter]:
    """Counter de lemas por empresa, somando todos os anos da janela."""
    por_empresa = defaultdict(Counter)
    for r in registros:
        por_empresa[r["empresa"]].update(_lemas_sem_autorreferencia(r["empresa"], r["lemas"]))
    return dict(por_empresa)


def agregar_por_empresa_ano(registros: list[dict]) -> dict[tuple[str, str], Counter]:
    """Counter de lemas por (empresa, ano) — base da evolução temporal."""
    por_empresa_ano = defaultdict(Counter)
    for r in registros:
        por_empresa_ano[(r["empresa"], r["ano"])].update(_lemas_sem_autorreferencia(r["empresa"], r["lemas"]))
    return dict(por_empresa_ano)


def top_termos(contador: Counter, n: int = 15) -> list[tuple[str, int]]:
    return contador.most_common(n)


def matriz_convergencia(por_empresa: dict[str, Counter], top_n: int = 50) -> dict[tuple[str, str], float]:
    """Similaridade de Jaccard entre os top-N termos de cada par de empresas.

    Jaccard = |interseção| / |união| dos conjuntos de termos mais
    frequentes. 0 = nenhum termo em comum entre os top-N; 1 = os mesmos
    termos exatos. É a métrica mais simples de "convergência temática"
    que dá pra calcular só com contagem de palavras (sem embeddings).
    """
    top_sets = {empresa: {t for t, _ in contador.most_common(top_n)} for empresa, contador in por_empresa.items()}
    empresas = sorted(top_sets)
    matriz = {}
    for i, a in enumerate(empresas):
        for b in empresas[i:]:
            inter = len(top_sets[a] & top_sets[b])
            uniao = len(top_sets[a] | top_sets[b])
            matriz[(a, b)] = inter / uniao if uniao else 0.0
    return matriz


def evolucao_termos(
    por_empresa_ano: dict[tuple[str, str], Counter], termos: list[str] = TERMOS_QUENTES
) -> dict[str, dict[tuple[str, str], float]]:
    """Frequência normalizada (por mil termos relevantes) de cada termo
    quente, por empresa e por ano — permite ver quando cada assunto
    "pegou" em cada blog.
    """
    resultado = {termo: {} for termo in termos}
    for (empresa, ano), contador in por_empresa_ano.items():
        total = sum(contador.values()) or 1
        for termo in termos:
            freq_por_mil = (contador.get(termo, 0) / total) * 1000
            resultado[termo][(empresa, ano)] = round(freq_por_mil, 2)
    return resultado
