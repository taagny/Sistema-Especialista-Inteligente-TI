"""Módulo de diagnóstico de lacunas de competências (skill gaps) e geração de roadmap de estudos."""

import math
from typing import Any, Dict, List, Optional


def analisar_skill_gaps(
    trilha: Dict[str, Any],
    autoavaliacao: Dict[str, Any],
    mapa_competencias: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compara os conhecimentos atuais do usuário com os requisitos mínimos de nível Júnior da trilha.

    Retorna um dicionário com:
        - prontidao_pct: percentual de prontidão (0 a 100%)
        - lacunas: lista de gaps ordenados por prioridade (lacuna * peso decrescente)
        - competencias_atendidas: lista de requisitos que o usuário já cumpre
        - total_lacunas: contagem de lacunas encontradas
    """
    requisitos = trilha.get("requisitos_junior", [])
    if not requisitos:
        return {
            "prontidao_pct": 100.0,
            "lacunas": [],
            "competencias_atendidas": [],
            "total_lacunas": 0,
        }

    pontos_exigidos = 0.0
    pontos_obtidos = 0.0
    lista_lacunas: List[Dict[str, Any]] = []
    lista_atendidas: List[Dict[str, Any]] = []

    for req in requisitos:
        comp_id = req["competencia"]
        nivel_minimo = int(req["nivel_minimo"])
        peso = float(req["peso"])

        nivel_atual = int(autoavaliacao.get(comp_id, 0))
        nivel_atual = max(0, min(3, nivel_atual))  # Garante escala 0 a 3

        pontos_exigidos += nivel_minimo * peso
        pontos_obtidos += min(nivel_atual, nivel_minimo) * peso

        nome_comp = comp_id
        desc_comp = ""
        if mapa_competencias and comp_id in mapa_competencias:
            nome_comp = mapa_competencias[comp_id].get("nome", comp_id)
            desc_comp = mapa_competencias[comp_id].get("descricao", "")

        lacuna = max(0, nivel_minimo - nivel_atual)
        prioridade = lacuna * peso

        item = {
            "competencia_id": comp_id,
            "nome": nome_comp,
            "descricao": desc_comp,
            "nivel_atual": nivel_atual,
            "nivel_exigido": nivel_minimo,
            "lacuna": lacuna,
            "peso": peso,
            "prioridade": prioridade,
        }

        if lacuna > 0:
            lista_lacunas.append(item)
        else:
            lista_atendidas.append(item)

    # Ordena lacunas por prioridade decrescente (maior gap e maior peso primeiro)
    lista_lacunas.sort(key=lambda x: (x["prioridade"], x["peso"]), reverse=True)

    prontidao = (pontos_obtidos / pontos_exigidos * 100.0) if pontos_exigidos > 0 else 100.0
    prontidao = round(min(100.0, max(0.0, prontidao)), 1)

    return {
        "prontidao_pct": prontidao,
        "lacunas": lista_lacunas,
        "competencias_atendidas": lista_atendidas,
        "total_lacunas": len(lista_lacunas),
    }


def gerar_roadmap_personalizado(
    trilha: Dict[str, Any],
    diagnostico_gaps: Dict[str, Any],
    horas_semanais: int = 10,
    horas_por_nivel_gap: int = 40,
) -> Dict[str, Any]:
    """Gera um plano de ação personalizado com base nas lacunas identificadas e tempo disponível."""
    lacunas = diagnostico_gaps.get("lacunas", [])
    prontidao = diagnostico_gaps.get("prontidao_pct", 0.0)
    dados_roadmap = trilha.get("roadmap", {})

    tecnologias_originais = dados_roadmap.get("tecnologias_prioritarias", [])
    todas_certificacoes = dados_roadmap.get("certificacoes", [])
    projetos = dados_roadmap.get("projetos_portfolio", [])

    # Estimativa de tempo em semanas
    total_gaps_niveis = sum(g["lacuna"] for g in lacunas)
    horas_totais_estimadas = total_gaps_niveis * horas_por_nivel_gap

    horas_semanais = max(1, horas_semanais)
    semanas_estimadas = math.ceil(horas_totais_estimadas / horas_semanais)

    # Seleção inteligente de certificações conforme maturidade
    certificacoes_recomendadas = []
    if prontidao < 50.0:
        # Foco inicial na primeira certificação (mais introdutória/conceitual)
        certificacoes_recomendadas = todas_certificacoes[:1] if todas_certificacoes else []
    else:
        # Usuário já tem base, pode visualizar todas as recomendações da trilha
        certificacoes_recomendadas = todas_certificacoes

    # Caso em que o usuário já cumpre todos os requisitos de Júnior
    apto_junior = len(lacunas) == 0

    if apto_junior:
        mensagem_status = (
            "Parabéns! Você já atende a todos os requisitos técnicos essenciais para posições de nível Júnior nesta trilha. "
            "Seu foco agora deve ser construir projetos robustos de portfólio e mirar no desenvolvimento de autonomia para o nível Pleno."
        )
        estimativa_texto = "Requisitos essenciais já concluídos. Foque no refinamento de portfólio e boas práticas."
    else:
        mensagem_status = (
            f"Você possui {len(lacunas)} competência(s) prioritária(s) a desenvolver para alcançar o patamar Júnior. "
            f"Com base na sua dedicação informada de {horas_semanais}h semanais, organizamos seu plano de estudos."
        )
        estimativa_texto = (
            f"Estimativa aproximada: cerca de {semanas_estimadas} semana(s) (~{horas_totais_estimadas}h de estudo prático) "
            f"com dedicação de {horas_semanais}h por semana. Vale lembrar que este ritmo varia com sua facilidade prévia e consistência."
        )

    return {
        "trilha_id": trilha.get("id"),
        "trilha_nome": trilha.get("nome"),
        "apto_junior": apto_junior,
        "prontidao_pct": prontidao,
        "mensagem_status": mensagem_status,
        "estimativa_tempo": {
            "horas_totais": horas_totais_estimadas,
            "horas_semanais": horas_semanais,
            "semanas_estimadas": semanas_estimadas,
            "texto_estimativa": estimativa_texto,
        },
        "tecnologias_prioritarias": tecnologias_originais,
        "certificacoes_recomendadas": certificacoes_recomendadas,
        "projetos_portfolio": projetos,
        "lacunas_priorizadas": lacunas,
    }
