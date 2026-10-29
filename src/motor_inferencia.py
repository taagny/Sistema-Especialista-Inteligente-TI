"""Motor de inferência baseado em regras com pontuação ponderada e penalidades."""

from typing import Any, Dict, List, Optional, Tuple


def normalizar_likert(valor: Any) -> float:
    """Normaliza uma resposta na escala Likert de 1 a 5 para o intervalo de 0.0 a 1.0.

    1 -> 0.0, 3 -> 0.5, 5 -> 1.0.
    Lança ValueError caso o valor não pertença à escala de 1 a 5.
    """
    if valor is None:
        raise ValueError("O valor de resposta não pode ser nulo.")

    try:
        num = float(valor)
    except (ValueError, TypeError) as erro:
        raise ValueError(f"Valor inválido para escala Likert: '{valor}'. Deve ser numérico.") from erro

    if not (1.0 <= num <= 5.0):
        raise ValueError(f"Valor fora da escala Likert de 1 a 5: {num}.")

    return (num - 1.0) / 4.0


def avaliar_condicao(valor_resposta: float, condicao: str, valor_limite: float) -> bool:
    """Avalia uma condição de conflito para aplicação de penalidade."""
    if condicao == "<=":
        return valor_resposta <= valor_limite
    if condicao == ">=":
        return valor_resposta >= valor_limite
    if condicao == "==":
        return valor_resposta == valor_limite
    if condicao == "<":
        return valor_resposta < valor_limite
    if condicao == ">":
        return valor_resposta > valor_limite
    raise ValueError(f"Operador condicional não suportado: '{condicao}'.")


def calcular_pontuacao_trilha(
    trilha: Dict[str, Any],
    respostas: Dict[str, Any],
    mapa_perguntas: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Calcula a pontuação bruta, máxima, compatibilidade base, penalidades e pontuação final de uma trilha.

    Respostas ausentes são ignoradas de forma proporcional (não diminuem a pontuação máxima respondida).
    """
    pesos: Dict[str, float] = trilha.get("pesos", {})
    pontos_obtidos = 0.0
    peso_maximo_respondido = 0.0
    contribuicoes: List[Dict[str, Any]] = []

    for id_pergunta, peso in pesos.items():
        if id_pergunta in respostas and respostas[id_pergunta] is not None:
            valor_bruto = respostas[id_pergunta]
            normalizado = normalizar_likert(valor_bruto)
            contribuicao = normalizado * peso
            pontos_obtidos += contribuicao
            peso_maximo_respondido += peso

            texto_pergunta = ""
            if mapa_perguntas and id_pergunta in mapa_perguntas:
                texto_pergunta = mapa_perguntas[id_pergunta].get("texto", "")

            contribuicoes.append(
                {
                    "id_pergunta": id_pergunta,
                    "texto": texto_pergunta,
                    "peso": peso,
                    "resposta": valor_bruto,
                    "normalizado": normalizado,
                    "contribuicao": round(contribuicao, 2),
                }
            )

    # Se nenhuma pergunta associada à trilha foi respondida, compatibilidade é 0
    if peso_maximo_respondido == 0.0:
        compatibilidade_base = 0.0
    else:
        compatibilidade_base = (pontos_obtidos / peso_maximo_respondido) * 100.0

    # Aplicação de penalidades lógicas
    penalidades_aplicadas: List[Dict[str, Any]] = []
    total_penalidades = 0.0

    for regra in trilha.get("penalidades", []):
        id_perg = regra["pergunta"]
        if id_perg in respostas and respostas[id_perg] is not None:
            val_resp = float(respostas[id_perg])
            if avaliar_condicao(val_resp, regra["condicao"], float(regra["valor"])):
                valor_pen = float(regra["penalidade"])
                total_penalidades += valor_pen
                penalidades_aplicadas.append(
                    {
                        "pergunta": id_perg,
                        "condicao": regra["condicao"],
                        "valor_limite": regra["valor"],
                        "resposta_usuario": val_resp,
                        "penalidade": valor_pen,
                        "motivo": regra["motivo"],
                    }
                )

    pontuacao_liquida = compatibilidade_base - total_penalidades
    pontuacao_final = max(0.0, min(100.0, pontuacao_liquida))

    # Ordena as maiores contribuições para justificar o resultado
    contribuicoes.sort(key=lambda x: x["contribuicao"], reverse=True)

    return {
        "id": trilha["id"],
        "nome": trilha["nome"],
        "descricao": trilha["descricao"],
        "pontuacao": round(pontuacao_final, 1),
        "pontuacao_base": round(compatibilidade_base, 1),
        "total_penalidades": round(total_penalidades, 1),
        "penalidades_aplicadas": penalidades_aplicadas,
        "contribuicoes": contribuicoes,
        "perguntas_destaque": contribuicoes[:3],
    }


def gerar_justificativa(item_trilha: Dict[str, Any]) -> str:
    """Gera uma explicação textual em linguagem natural sobre o porquê da pontuação obtida."""
    destaques = item_trilha.get("perguntas_destaque", [])
    penalidades = item_trilha.get("penalidades_aplicadas", [])

    frases: List[str] = []

    # Aspectos positivos
    positivos = [d for d in destaques if d["resposta"] >= 4]
    if positivos:
        nomes = [d["id_pergunta"].replace("_", " ") for d in positivos]
        if len(nomes) == 1:
            frases.append(f"Seu alto interesse em {nomes[0]} foi o principal impulsionador desta trilha.")
        else:
            frases.append(f"Suas afinidades com {', '.join(nomes[:-1])} e {nomes[-1]} puxaram esta compatibilidade para cima.")
    elif destaques:
        frases.append("Pontuação base equilibrada com base nas suas preferências gerais.")

    # Penalidades aplicadas
    if penalidades:
        for p in penalidades:
            frases.append(f"Penalidade aplicada (-{p['penalidade']:.0f}%): {p['motivo']}")

    return " ".join(frases) if frases else "Compatibilidade calculada de acordo com as respostas fornecidas."


def verificar_empates(
    ranking: List[Dict[str, Any]], tolerancia_pct: float
) -> Tuple[bool, List[Dict[str, Any]], Optional[str]]:
    """Identifica se existem empates parciais entre as primeiras posições do ranking."""
    if len(ranking) < 2:
        return False, [], None

    empates: List[Dict[str, Any]] = []
    for i in range(min(2, len(ranking) - 1)):
        trilha_a = ranking[i]
        trilha_b = ranking[i + 1]
        dif = abs(trilha_a["pontuacao"] - trilha_b["pontuacao"])

        if dif <= tolerancia_pct:
            empates.append(
                {
                    "posicao_a": i + 1,
                    "trilha_a": trilha_a["nome"],
                    "pontuacao_a": trilha_a["pontuacao"],
                    "posicao_b": i + 2,
                    "trilha_b": trilha_b["nome"],
                    "pontuacao_b": trilha_b["pontuacao"],
                    "diferenca": round(dif, 1),
                }
            )

    if empates:
        primeiro_empate = empates[0]
        msg = (
            f"Detectamos um empate técnico / perfil híbrido entre {primeiro_empate['trilha_a']} "
            f"({primeiro_empate['pontuacao_a']}%) e {primeiro_empate['trilha_b']} "
            f"({primeiro_empate['pontuacao_b']}%), com diferença de apenas {primeiro_empate['diferenca']}%. "
            f"Seus interesses transitam muito bem entre essas duas áreas."
        )
        return True, empates, msg

    return False, [], None


def calcular_ranking(respostas: Dict[str, Any], base: Dict[str, Any]) -> Dict[str, Any]:
    """Função pura que calcula o ranking completo das trilhas, gera o Top 3 com justificativas e verifica empates.

    Parâmetros:
        respostas: dicionário com as respostas do usuário (ex: {'logica_algoritmos': 5, ...})
        base: base de conhecimento carregada e validada

    Retorna:
        dicionário estruturado com ranking, top3, empates e parâmetros utilizados.
    """
    mapa_perguntas = {p["id"]: p for p in base.get("perguntas", [])}
    trilhas = base.get("trilhas", [])
    tolerancia = float(base.get("parametros", {}).get("tolerancia_empate_pct", 3.0))

    resultados_trilhas: List[Dict[str, Any]] = []
    for trilha in trilhas:
        res_trilha = calcular_pontuacao_trilha(trilha, respostas, mapa_perguntas)
        resultados_trilhas.append(res_trilha)

    # Ordenação por pontuação decrescente, e por pontuação_base como critério de desempate
    resultados_trilhas.sort(
        key=lambda x: (x["pontuacao"], x["pontuacao_base"]),
        reverse=True,
    )

    # Atribuição de posição formal no ranking e geração de justificativa
    ranking_formatado: List[Dict[str, Any]] = []
    for idx, item in enumerate(resultados_trilhas, start=1):
        item["posicao"] = idx
        item["justificativa"] = gerar_justificativa(item)
        ranking_formatado.append(item)

    tem_empate, detalhes_empate, mensagem_empate = verificar_empates(ranking_formatado, tolerancia)

    top3 = ranking_formatado[:3]

    return {
        "ranking": ranking_formatado,
        "top3": top3,
        "empate_parcial": tem_empate,
        "detalhes_empate": detalhes_empate,
        "mensagem_empate": mensagem_empate,
        "total_trilhas": len(ranking_formatado),
    }
