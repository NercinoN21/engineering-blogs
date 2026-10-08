# Convergência e divergência temática entre blogs de engenharia

Projeto da disciplina **Modelagem de Dados Não Estruturados** (UFPB).
Coleta posts de 7 blogs de engenharia de grandes empresas de tecnologia,
com título, data de publicação e conteúdo, e guarda tudo em um banco
TinyDB (`data/posts.json`) para uma análise futura de convergência e
divergência temática ao longo do tempo (ver `../docs/atividade_extra_tema_projeto.pdf`).

Para uma explicação não técnica (e algumas notas técnicas extras para
quem já manja), veja
[`../docs/explicando_para_uma_crianca_de_10_anos.md`](../docs/explicando_para_uma_crianca_de_10_anos.md).

## Resultado da coleta (última execução completa)

| Empresa   | Posts salvos | Técnica                                   |
|-----------|-------------:|---------------------------------------------|
| Meta      | 274          | API REST do WordPress                      |
| Uber      | 237          | Selenium (paginação em JS) + requests/BS4  |
| Shopify   | 202          | Feed Atom completo + requests/BS4          |
| Microsoft | 157          | API REST do WordPress (devblogs.../ise)    |
| Spotify   | 117          | Selenium ("load more") + requests/BS4      |
| GitHub    | 92           | API REST do WordPress (categoria Engineering) |
| Slack     | 78           | API REST do WordPress                      |
| **Total** | **1157**     |                                               |

Todos dentro da janela de 5 anos (2021–2026). Rode `python -m blogs_engenharia.cli.stats`
para ver esses números atualizados (contagem por ano, tamanho médio de
conteúdo, e um alerta automático se algum post tiver conteúdo
suspeitosamente curto — útil pra pegar erro de extração).

### Fontes testadas e descartadas

Antes de chegar nesses 7, testei outras fontes e descartei as que não
davam uma amostra boa o suficiente (menos de ~30 posts na janela de 5
anos) ou que não funcionaram de forma confiável:

| Fonte  | O que aconteceu |
|--------|------------------|
| **Dropbox Tech** | Só 29 posts — bloqueado por um AWS WAF depois de poucas dezenas de requisições, mesmo com delay generoso. Dropbox não entrou na lista final; a investigação ficou registrada no documento "explicando para uma criança". |
| **Netflix Tech Blog** | Só 10 posts — hospedado no Medium, que limita o RSS aos itens mais recentes e bloqueia (HTTP 403 / desafio Cloudflare) tanto `curl` quanto Selenium nas páginas de arquivo. |
| **Airbnb Engineering** | Mesmo problema do Netflix (também é Medium). |
| **Apple (Machine Learning Research)** | Mesmo padrão "estilo Medium": RSS devolve só 10 itens recentes, sem paginação confiável. Descartado pelo mesmo motivo do Netflix/Airbnb. |
| **Oracle** (`blogs.oracle.com`) | HTTP 403 em qualquer requisição — bloqueado de cara, nem testei mais a fundo. |

## Blogs coletados e técnica usada em cada um

| Empresa   | Fonte dos links                                  | Descoberta  | Extração do conteúdo |
|-----------|----------------------------------------------------|--------------|------------------------|
| Meta      | API REST do WordPress (`engineering.fb.com`)       | requests (JSON) | já vem no JSON (`content.rendered`) |
| Microsoft | API REST do WordPress (`devblogs.microsoft.com/ise`) | requests (JSON) | já vem no JSON |
| GitHub    | API REST do WordPress, filtrada por categoria "Engineering" (`github.blog`) | requests (JSON) | já vem no JSON |
| Slack     | API REST do WordPress (`slack.engineering`)        | requests (JSON) | já vem no JSON |
| Shopify   | Feed Atom completo (`shopify.engineering/blog.atom`) | `feedparser` (1 request só) | requests + BeautifulSoup |
| Spotify   | Botão "load more" (Next.js, client-side)           | **Selenium** | requests + BeautifulSoup |
| Uber      | Paginação `/page/N/` (React, client-side)          | **Selenium** | requests + BeautifulSoup |

Cada blog tem uma arquitetura diferente, então cada um tem seu próprio
módulo em `scraper/blogs/`, com uma docstring no topo explicando como o
site funciona e por que aquela técnica foi escolhida (o resultado de uma
investigação manual com `curl` antes de escrever qualquer código).
Meta, Microsoft, GitHub e Slack compartilham a mesma lógica de paginação da API
REST do WordPress via `scraper/blogs/_wordpress_common.py` — não faz sentido
reescrever o mesmo loop de paginação 4 vezes.

### Por que `devblogs.microsoft.com/ise` e não "o blog da Microsoft"?

A Microsoft não tem um blog de engenharia único: `devblogs.microsoft.com`
hospeda dezenas de blogs separados (`/dotnet`, `/typescript`,
`/oldnewthing`, `/powershell`...), cada um focado numa linguagem/produto
(mais changelog de release do que "como resolvemos esse problema de
escala"). `/ise` (**Industry Solutions Engineering**, o time que
trabalha em projetos de engenharia com clientes da Microsoft) é o mais
parecido em espírito com os outros blogs deste projeto — por isso foi o
escolhido. Ver docstring de `scraper/blogs/microsoft.py` para mais
detalhes.

### Por que `github.blog` filtrado por categoria, e não o blog inteiro?

`github.blog` publica muito mais que engenharia (produto, comunidade,
changelogs de feature) — 4.152 posts no total, sem filtro. A categoria
"Engineering" (id 72 na API REST do WordPress) sozinha tem 175 posts e é
o conteúdo que de fato se compara aos outros blogs do projeto.

## Por que Selenium para Uber e Spotify, e não para os outros?

Selenium só é necessário quando o conteúdo é montado em JavaScript no
navegador (SPA/React/Next.js client-side) e não existe uma API ou feed
alternativo. Isso foi confirmado testando cada site manualmente:

- **Uber**: `curl` na listagem devolve HTML quase vazio (sem links de
  post); com Selenium aparecem os posts **e** um botão "next" que leva a
  `/page/2/`, `/page/3/`... → paginação escondida atrás de JS.
- **Spotify**: a listagem usa um botão "load more" sem paginação por URL;
  com Selenium, clicando nele repetidamente, saem 117 posts dentro da
  janela de 5 anos.
- Nos dois casos, a **página de cada post individual** já vem pronta no
  HTML (renderizada no servidor), então usamos `requests` simples para
  baixar o conteúdo — só a *listagem* precisa de navegador.
- Meta, Microsoft, GitHub e Slack não precisaram de Selenium nem de
  parsing HTML: a própria API REST do WordPress já devolve o conteúdo
  pronto em JSON. Shopify também não precisou de Selenium — um feed
  Atom simples já lista o histórico completo.

## Janela temporal da amostra: por que 5 anos

Dado o tema "convergência/divergência ao longo do tempo", a amostra
precisa cobrir um período em comum entre todos os blogs, senão a
comparação fica injusta (um blog mais antigo "venceria" por ter mais
dados, não por falar mais do assunto). Os 7 blogs escolhidos já existiam
e publicavam com regularidade há pelo menos 5 anos. Por isso a janela
padrão é **os últimos 5 anos** (`scraper/config.py::JANELA_EM_ANOS`).

## Controle de qualidade dos dados

Dois problemas reais apareceram durante os testes e foram corrigidos no
código (não só ignorados):

1. **Bloqueio silencioso** (visto no Dropbox, por isso ele não entrou na
   lista final): alguns sites, ao perceber um robô fazendo muitas
   requisições seguidas, não devolvem um erro HTTP — devolvem uma
   resposta "de sucesso" só que vazia. `scraper/utils.py::polite_get`
   detecta corpo vazio/curto demais e cabeçalhos de WAF conhecidos, e
   trata como falha.
2. **Posts-ponteiro** (visto no Meta): alguns posts na API REST do
   WordPress têm `content.rendered` vazio porque o artigo de verdade
   mora em outro domínio da empresa. `scraper/blogs/_wordpress_common.py`
   e `scraper/blogs/{uber,spotify,shopify}.py` descartam qualquer post
   com menos de 150 caracteres de conteúdo extraído.

`python -m blogs_engenharia.cli.stats` reaplica essa mesma checagem nos
dados já salvos, como uma segunda linha de defesa.

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # tinydb, feedparser, lxml, selenium, bs4, requests
python -m spacy download en_core_web_sm

# Selenium precisa do Google Chrome instalado (o driver é baixado
# automaticamente pelo próprio Selenium 4.6+, não precisa instalar
# chromedriver à parte):
#   brew install --cask google-chrome

PYTHONPATH=src python -m blogs_engenharia.cli.scrape                     # roda os 7 blogs
PYTHONPATH=src python -m blogs_engenharia.cli.scrape --blogs slack meta  # roda só alguns
PYTHONPATH=src python -m blogs_engenharia.cli.scrape --list              # lista os blogs válidos
PYTHONPATH=src python -m blogs_engenharia.cli.stats                      # resumo do que foi coletado
```

Rodar de novo não duplica posts: cada post é salvo com `upsert` usando a
URL como chave (`scraper/database.py`), então o script pode ser
interrompido e reexecutado sem problema.

## Análise de PLN (RE + spaCy)

Depois de coletados, os posts são analisados com **expressões
regulares (RE)** e **spaCy** (`src/blogs_engenharia/nlp/`), respondendo uma
versão mais simples — mas já concreta — da pergunta de pesquisa do tema: os
blogs convergem ou divergem ao longo do tempo?

```bash
PYTHONPATH=src python -m blogs_engenharia.cli.analyze              # processa os 1157 posts (~5 minutos)
PYTHONPATH=src python -m blogs_engenharia.cli.analyze --limite 50  # só os 50 primeiros, pra testar rápido
```

**O que o RE faz** (`nlp/preprocess.py`): limpa URLs/e-mails antes de
mandar o texto pro spaCy, e extrai siglas de tecnologia (API, AWS, SQL,
ML...) com o padrão `\b[A-Z][A-Z0-9]{1,5}\b` — o modelo de NER do spaCy
(treinado em texto jornalístico genérico) erra ou ignora boa parte
dessas siglas, então um padrão de regex simples complementa bem.

**O que o spaCy faz** (`nlp/pipeline.py`): tagging (POS) + lematização +
reconhecimento de entidades (`en_core_web_sm`, com o componente `parser`
desligado). De cada post, extraímos os substantivos/substantivos próprios
lematizados (ex.: "scaling"/"scaled" viram "scale"), sem stopwords.

**Duas análises** (`nlp/aggregate.py`):

1. **Matriz de convergência** — similaridade de Jaccard entre os top-50
   termos de cada par de empresas. Resultado atual: todos os pares ficam
   entre 0.25 e 0.39; Meta e Shopify são o par mais parecido (0.39).
2. **Evolução de termos quentes** — frequência normalizada (por mil
   termos relevantes) de um punhado de termos de interesse, por ano,
   somando as 7 empresas. Resultado atual, o mais claro do projeto: o
   termo **"ai" sobe de 0.3 (2021) para 5.6 (2026)** e **"llm" sai de 0
   (2021) para 2.8 (2026)**.

Os resultados ficam salvos em 4 tabelas novas no mesmo `data/posts.json`
(`nlp_termos_por_post`, `nlp_resumo_empresa`, `nlp_convergencia`,
`nlp_evolucao_termos`) e também são impressos no terminal ao rodar.

## Estrutura de cada documento salvo no TinyDB

```json
{
  "empresa": "Slack",
  "titulo": "Shipyard: How We Built Slack's Next-Generation EC2 Platform",
  "url": "https://slack.engineering/shipyard-...",
  "data_publicacao": "2026-07-14",
  "conteudo": "texto completo do post, limpo de tags HTML...",
  "janela_amostral": "5_anos"
}
```

## Estrutura do código

Este diretório (`blogs-engenharia/`) é o pacote em si. `docs/` e
`CLAUDE.md` ficam um nível acima, fora do pacote.

```
src/blogs_engenharia/
  scraper/
    config.py            # janela temporal, caminhos, cabeçalhos HTTP
    database.py           # abre o TinyDB e faz upsert sem duplicar
    utils.py               # sessão requests, driver Selenium, limpeza de texto
    blogs/
      _wordpress_common.py  # paginação da API REST do WordPress (Meta/Microsoft/GitHub/Slack)
      meta.py                 # engineering.fb.com
      microsoft.py             # devblogs.microsoft.com/ise
      github.py                 # github.blog, categoria Engineering
      slack.py                   # slack.engineering
      shopify.py                  # feed Atom + BeautifulSoup
      spotify.py                   # Selenium (load more) + BeautifulSoup
      uber.py                       # Selenium (paginação) + BeautifulSoup
  nlp/
    preprocess.py            # limpeza + extração de siglas via RE
    pipeline.py                # tagging/lematização/NER via spaCy
    aggregate.py                 # agregação por empresa/ano, Jaccard, termos quentes
  cli/
    scrape.py               # orquestrador da coleta
    analyze.py                # orquestrador da análise de PLN
    stats.py                    # conferência rápida pós-coleta
data/posts.json           # banco TinyDB (posts + resultados de PLN)
```

## Próximos passos (fora do escopo desta entrega)

A versão mais ambiciosa da pergunta de pesquisa do tema — representar a
convergência/divergência como uma **rede ou série temporal de
similaridade vetorial via embeddings** (ex.: `sentence-transformers`,
em vez da contagem de termos/Jaccard usada aqui) — fica para uma etapa
futura do trabalho.
