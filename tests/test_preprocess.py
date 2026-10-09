from blogs_engenharia.nlp.preprocess import extrair_siglas, limpar_para_nlp


def test_limpar_para_nlp_remove_urls_e_emails():
    texto = "Veja em https://exemplo.com/post e fale com a gente em time@exemplo.com, obrigado."
    limpo = limpar_para_nlp(texto)

    assert "https://" not in limpo
    assert "@" not in limpo


def test_limpar_para_nlp_trunca_no_limite_de_caracteres():
    texto = "a" * 100

    assert len(limpar_para_nlp(texto, limite_caracteres=10)) == 10


def test_extrair_siglas_conta_tecnologias_e_ignora_siglas_genericas():
    contador = extrair_siglas("Usamos API e AWS. O time ficou OK, squad A VS squad B. Ver Parte II.")

    assert contador["API"] == 1
    assert contador["AWS"] == 1
    assert "OK" not in contador
    assert "VS" not in contador
    assert "II" not in contador
    assert "A" not in contador
