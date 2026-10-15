FROM python:3.12-slim

# Chromium + driver: necessários pros coletores de Spotify e Uber, que
# dependem de Selenium (sites com conteúdo montado em JavaScript — ver
# README.md). CHROME_BIN avisa o Selenium onde o binário está, já que
# aqui não é "google-chrome" como numa instalação normal fora do Docker
# (ver blogs_engenharia/scraper/utils.py::make_driver).
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir -e . \
    && python -m spacy download en_core_web_sm

COPY tests ./tests

CMD ["blogs-engenharia-scrape", "--list"]
