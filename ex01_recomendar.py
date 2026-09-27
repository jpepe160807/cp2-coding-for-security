# Exercicio 1 - recomenda banco, lado do CAP e risco OWASP a partir do perfil


def recomendar(perfil):
    if perfil["schema_fixo"] and perfil["precisa_acid"]:
        banco = "MySQL"
    else:
        banco = "MongoDB"

    if perfil["tolera_atraso_de_consistencia"]:
        cap = "AP"
    else:
        cap = "CP"

    # a justificativa tem que dizer qual erro seria inaceitavel no cenario
    if perfil["precisa_acid"] and perfil["dado_sensivel"]:
        justificativa = "autenticar errado e pior do que ficar fora do ar"
    elif not perfil["precisa_acid"] and perfil["tolera_atraso_de_consistencia"]:
        justificativa = "perder 1s de log e melhor do que parar de aceitar log"
    elif perfil["dado_sensivel"] and cap == "CP":
        justificativa = "auditoria divergente nao vale como prova"
    else:
        justificativa = "a consistencia da transacao vale mais que disponibilidade extra"

    if perfil["dado_sensivel"] and perfil["precisa_acid"]:
        risco_owasp = "A07"
    elif perfil["dado_sensivel"] and cap == "CP":
        risco_owasp = "A08"
    else:
        risco_owasp = "A09"

    return {
        "banco": banco,
        "cap": cap,
        "justificativa": justificativa,
        "risco_owasp": risco_owasp,
    }


perfis = {
    "credenciais_do_SOC":     {"schema_fixo": True,  "precisa_acid": True,  "escala_horizontal": False, "tolera_atraso_de_consistencia": False, "dado_sensivel": True},
    "telemetria_de_sensores": {"schema_fixo": False, "precisa_acid": False, "escala_horizontal": True,  "tolera_atraso_de_consistencia": True,  "dado_sensivel": False},
    "trilha_de_auditoria":    {"schema_fixo": False, "precisa_acid": False, "escala_horizontal": True,  "tolera_atraso_de_consistencia": False, "dado_sensivel": True},
    "carrinho_de_licencas":   {"schema_fixo": True,  "precisa_acid": True,  "escala_horizontal": False, "tolera_atraso_de_consistencia": False, "dado_sensivel": False},
    "cache_de_sessoes":       {"schema_fixo": True,  "precisa_acid": False, "escala_horizontal": True,  "tolera_atraso_de_consistencia": True,  "dado_sensivel": True},
}


if __name__ == "__main__":
    for nome, perfil in perfis.items():
        r = recomendar(perfil)
        print(f"{nome:24} -> {r['banco']:7} | {r['cap']} | {r['justificativa']} | {r['risco_owasp']}")
