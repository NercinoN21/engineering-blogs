"""Classes falsas (fakes nomeados) que simulam I/O externo (HTTP) nos
testes, sem rede real — ver regra de testes em CLAUDE.md ("mock external
I/O... with named fake classes, not inline stubs").
"""

from __future__ import annotations


class FakeWordPressResponse:
    """Imita a parte da interface de `requests.Response` usada pelo scraper."""

    def __init__(self, payload: list[dict] | None, status_code: int = 200):
        self._payload = payload or []
        self.status_code = status_code
        self.headers: dict[str, str] = {}
        self.content = b"x" * 100 if payload else b""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> list[dict]:
        return self._payload


class FakeWordPressSession:
    """Simula `requests.Session` para a API REST do WordPress paginada.

    `paginas` é uma lista de páginas (cada uma, uma lista de posts no
    formato da API). Pedir uma página além da última devolve uma lista
    vazia, igual a API real faz quando `page` passa do total.
    """

    def __init__(self, paginas: list[list[dict]]):
        self.paginas = paginas
        self.chamadas: list[dict] = []

    def get(self, url: str, params: dict | None = None, timeout: int | None = None, **kwargs) -> FakeWordPressResponse:
        self.chamadas.append(params or {})
        pagina_num = (params or {}).get("page", 1)
        indice = pagina_num - 1
        if indice >= len(self.paginas):
            return FakeWordPressResponse([])
        return FakeWordPressResponse(self.paginas[indice])
