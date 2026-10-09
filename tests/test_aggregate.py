from collections import Counter

from blogs_engenharia.nlp.aggregate import (
    agregar_por_empresa,
    evolucao_termos,
    matriz_convergencia,
)


def test_agregar_por_empresa_remove_autorreferencia_mas_mantem_o_resto():
    registros = [
        {"empresa": "Uber", "lemas": ["uber", "scale", "database"]},
        {"empresa": "Uber", "lemas": ["uber", "scale"]},
    ]

    por_empresa = agregar_por_empresa(registros)

    assert "uber" not in por_empresa["Uber"]
    assert por_empresa["Uber"]["scale"] == 2
    assert por_empresa["Uber"]["database"] == 1


def test_matriz_convergencia_calcula_jaccard_dos_top_termos():
    por_empresa = {
        "A": Counter({"x": 10, "y": 5}),
        "B": Counter({"x": 10, "z": 5}),
    }

    matriz = matriz_convergencia(por_empresa, top_n=2)

    # top-2 de A = {x, y}, top-2 de B = {x, z} -> interseção 1, união 3
    assert matriz[("A", "B")] == 1 / 3
    assert matriz[("A", "A")] == 1.0


def test_evolucao_termos_normaliza_frequencia_por_mil():
    por_empresa_ano = {("A", "2026"): Counter({"ai": 1, "outro": 9})}

    evolucao = evolucao_termos(por_empresa_ano, termos=["ai"])

    assert evolucao["ai"][("A", "2026")] == 100.0
