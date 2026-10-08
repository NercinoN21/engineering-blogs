"""Limpeza e extração baseada em expressões regulares (RE), que roda
*antes* do spaCy (`nlp/pipeline.py`).

Por que precisa de RE além do spaCy: os posts são textos técnicos cheios
de URLs, trechos de código colados no meio da prosa (os posts foram
salvos como texto puro, sem as tags <code>/<pre> originais) e siglas de
tecnologia (API, AWS, gRPC, K8s...). Isso teria dois efeitos ruins se
fosse direto pro spaCy sem limpeza: (1) URLs e lixo de código viram
"palavras" na contagem de frequência, poluindo os termos mais comuns;
(2) o modelo de NER do spaCy (treinado em texto jornalístico genérico,
não em jargão de engenharia) erra ou ignora boa parte das siglas de
tecnologia — por isso extraímos siglas separadamente, com um padrão de
regex, em vez de depender só do reconhecimento de entidades do spaCy.
"""

import re
from collections import Counter

_URL = re.compile(r"https?://\S+")
_EMAIL = re.compile(r"\S+@\S+\.\S+")
_ESPACOS = re.compile(r"\s+")

# Sigla: 2 a 6 letras/dígitos maiúsculos, pelo menos uma letra (exclui
# números puros tipo "404"). Cobre API, AWS, SQL, gRPC (como "GRPC" após
# upper() não é usado aqui — mantemos o case original), K8S, CI, CD, ML, AI...
_SIGLA = re.compile(r"\b[A-Z][A-Z0-9]{1,5}\b")

# Siglas comuns que aparecem em texto técnico mas não dizem nada sobre o
# ASSUNTO do post (números romanos de "Parte II", abreviações genéricas
# de escrita em inglês etc.) — ficam de fora da contagem de tecnologias.
_SIGLAS_IGNORADAS = {
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "A", "OK", "ETC", "VS", "FAQ", "TL", "DR", "PS", "ie", "eg",
}


def limpar_para_nlp(texto: str, limite_caracteres: int = 20_000) -> str:
    """Remove URLs/e-mails e normaliza espaços antes de mandar pro spaCy.

    Trunca em `limite_caracteres` (post mais longo da coleta tem ~42 mil
    caracteres) só por controle de tempo de processamento — o começo de
    um post de engenharia normalmente já concentra os termos principais
    (título, contexto do problema), então truncar o final não distorce
    muito a análise de frequência de termos.
    """
    texto = _URL.sub(" ", texto)
    texto = _EMAIL.sub(" ", texto)
    texto = _ESPACOS.sub(" ", texto).strip()
    return texto[:limite_caracteres]


def extrair_siglas(texto: str) -> Counter:
    """Conta siglas em maiúsculas (API, AWS, SQL, ML, CI, CD...) via regex.

    Complementa o spaCy: siglas de tecnologia raramente são reconhecidas
    corretamente pelo NER genérico (`en_core_web_sm`), mas são um sinal
    forte de "do que esse post fala" — e são fáceis de pegar com um
    padrão de regex simples, sem precisar de um modelo de linguagem.
    """
    candidatas = _SIGLA.findall(texto)
    return Counter(s for s in candidatas if s not in _SIGLAS_IGNORADAS)
