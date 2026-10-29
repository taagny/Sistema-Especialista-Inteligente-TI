"""Testes unitários para análise de gaps de competências e roadmap de desenvolvimento."""

import pytest
from src.base_conhecimento import carregar_base_conhecimento
from src.gaps_roadmap import analisar_skill_gaps, gerar_roadmap_personalizado


@pytest.fixture
def base():
    return carregar_base_conhecimento()


@pytest.fixture
def trilha_backend(base):
    return next(t for t in base["trilhas"] if t["id"] == "backend")


def test_analise_gaps_iniciante_absoluto(trilha_backend):
    """Usuário sem nenhum conhecimento prévio deve ter 0% de prontidão e todos os gaps listados."""
    autoavaliacao = {comp: 0 for comp in ["python", "sql", "git", "linux", "apis_rest", "docker"]}
    diagnostico = analisar_skill_gaps(trilha_backend, autoavaliacao)

    assert diagnostico["prontidao_pct"] == 0.0
    assert diagnostico["total_lacunas"] == len(trilha_backend["requisitos_junior"])
    assert len(diagnostico["competencias_atendidas"]) == 0

    roadmap = gerar_roadmap_personalizado(trilha_backend, diagnostico, horas_semanais=10)
    assert roadmap["apto_junior"] is False
    assert roadmap["estimativa_tempo"]["semanas_estimadas"] > 0
    # Como prontidão é 0%, deve sugerir apenas a certificação inicial
    assert len(roadmap["certificacoes_recomendadas"]) == 1


def test_analise_gaps_usuario_experiente(trilha_backend):
    """Usuário que já domina as tecnologias exigidas deve ter 100% de prontidão e 0 gaps."""
    autoavaliacao = {
        "python": 3,
        "sql": 3,
        "apis_rest": 3,
        "git": 3,
        "testes_automatizados": 3,
        "docker": 3,
    }
    diagnostico = analisar_skill_gaps(trilha_backend, autoavaliacao)

    assert diagnostico["prontidao_pct"] == 100.0
    assert diagnostico["total_lacunas"] == 0
    assert len(diagnostico["competencias_atendidas"]) == len(trilha_backend["requisitos_junior"])

    roadmap = gerar_roadmap_personalizado(trilha_backend, diagnostico, horas_semanais=10)
    assert roadmap["apto_junior"] is True
    assert "Pleno" in roadmap["mensagem_status"]
    assert len(roadmap["certificacoes_recomendadas"]) >= 1


def test_prioridade_ordenacao_lacunas(trilha_backend):
    """Gaps com maior produto de lacuna * peso devem encabeçar a lista de prioridades."""
    # Requisitos do backend:
    # python (exige 2, peso 5) -> se tiver 0, lacuna=2, prio=10
    # docker (exige 1, peso 2) -> se tiver 0, lacuna=1, prio=2
    # git (exige 2, peso 3) -> se tiver 1, lacuna=1, prio=3
    autoavaliacao = {
        "python": 0,
        "sql": 2,  # atendido
        "apis_rest": 2,  # atendido
        "git": 1,
        "docker": 0,
        "testes_automatizados": 1,  # atendido
    }
    diagnostico = analisar_skill_gaps(trilha_backend, autoavaliacao)

    assert 0.0 < diagnostico["prontidao_pct"] < 100.0
    lacunas = diagnostico["lacunas"]
    assert len(lacunas) == 3

    # Python deve ser a maior prioridade (lacuna 2 * peso 5 = 10)
    assert lacunas[0]["competencia_id"] == "python"
    assert lacunas[0]["prioridade"] == 10.0


def test_estimativa_tempo_proporcional_dedicacao(trilha_backend):
    """Se o usuário dobra as horas de estudo por semana, o tempo em semanas deve cair pela metade."""
    autoavaliacao = {"python": 0, "sql": 0, "git": 0, "apis_rest": 0}
    diagnostico = analisar_skill_gaps(trilha_backend, autoavaliacao)

    roadmap_10h = gerar_roadmap_personalizado(trilha_backend, diagnostico, horas_semanais=10)
    roadmap_20h = gerar_roadmap_personalizado(trilha_backend, diagnostico, horas_semanais=20)

    semanas_10h = roadmap_10h["estimativa_tempo"]["semanas_estimadas"]
    semanas_20h = roadmap_20h["estimativa_tempo"]["semanas_estimadas"]

    assert semanas_20h <= (semanas_10h // 2) + 1
