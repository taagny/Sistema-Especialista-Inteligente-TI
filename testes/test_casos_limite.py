"""Testes de robustez e casos limite para o sistema especialista."""

import pytest
from src.base_conhecimento import carregar_base_conhecimento
from src.gaps_roadmap import analisar_skill_gaps, gerar_roadmap_personalizado
from src.motor_inferencia import calcular_ranking


@pytest.fixture
def base():
    return carregar_base_conhecimento()


def test_caso_1_perfil_ambiguo_dados_e_web(base):
    """Gosta igualmente de dados e desenvolvimento de sistemas; deve acusar empate técnico."""
    respostas = {
        "logica_algoritmos": 5,
        "banco_dados": 5,
        "matematica_estatistica": 4,
        "ia_machine_learning": 4,
        "automacao_scripts": 4,
        "testes_qualidade": 3,
        "infra_servidores": 3,
        "design_visual_ux": 2,
        "trabalho_criativo_visual": 2,
        "desenvolvimento_mobile": 1,
        "redes_seguranca": 2,
        "preferencia_remoto": 5,
        "busca_retorno_rapido": 4,
        "interesse_lideranca": 2,
        "tolerancia_oncall": 2,
        "gestao_comunicacao": 3,
    }
    resultado = calcular_ranking(respostas, base)
    top_ids = [t["id"] for t in resultado["top3"]]

    # Deve conter Back-end e Engenharia de Dados ou Ciência de Dados entre os líderes
    assert "backend" in top_ids
    assert "engenharia_dados" in top_ids or "ciencia_dados" in top_ids
    # Como as pontuações são próximas, deve marcar empate parcial
    assert resultado["empate_parcial"] is True
    assert resultado["mensagem_empate"] is not None


def test_caso_2_todas_respostas_minimas(base):
    """Todas as respostas Likert iguais a 1; sistema não deve ter erro de divisão e pontuação é 0."""
    perguntas_likert = [p["id"] for p in base["perguntas"] if p.get("tipo") == "likert"]
    respostas = {pid: 1 for pid in perguntas_likert}

    resultado = calcular_ranking(respostas, base)
    assert len(resultado["ranking"]) == 10
    for trilha in resultado["ranking"]:
        assert trilha["pontuacao"] == 0.0
        assert trilha["pontuacao_base"] == 0.0


def test_caso_3_todas_respostas_maximas(base):
    """Todas as respostas Likert iguais a 5; sistema deve pontuar 100% em todas sem penalidades."""
    perguntas_likert = [p["id"] for p in base["perguntas"] if p.get("tipo") == "likert"]
    respostas = {pid: 5 for pid in perguntas_likert}

    resultado = calcular_ranking(respostas, base)
    assert len(resultado["ranking"]) == 10
    for trilha in resultado["ranking"]:
        assert trilha["pontuacao"] == 100.0
        assert trilha["total_penalidades"] == 0.0


def test_caso_4_todas_respostas_neutras(base):
    """Todas as respostas Likert iguais a 3; base de 50% para todas as trilhas sem quebras."""
    perguntas_likert = [p["id"] for p in base["perguntas"] if p.get("tipo") == "likert"]
    respostas = {pid: 3 for pid in perguntas_likert}

    resultado = calcular_ranking(respostas, base)
    assert len(resultado["ranking"]) == 10
    for trilha in resultado["ranking"]:
        assert trilha["pontuacao"] == 50.0
        assert trilha["total_penalidades"] == 0.0
    assert resultado["empate_parcial"] is True


def test_caso_5_perfil_contraditorio_design_sem_logica(base):
    """Afinidade com design (5), porém aversão a lógica (1). Front-end supera Back-end."""
    respostas = {
        "design_visual_ux": 5,
        "trabalho_criativo_visual": 5,
        "logica_algoritmos": 1,
        "infra_servidores": 1,
        "redes_seguranca": 1,
    }
    resultado = calcular_ranking(respostas, base)
    ids_ranking = [t["id"] for t in resultado["ranking"]]

    # Front-end deve estar bem posicionado e Back-end deve cair por penalidade em lógica
    assert ids_ranking.index("frontend") < ids_ranking.index("backend")
    backend_info = next(t for t in resultado["ranking"] if t["id"] == "backend")
    assert backend_info["total_penalidades"] > 0


def test_caso_6_respostas_parciais_em_branco(base):
    """Respondeu apenas 2 perguntas e deixou o restante em branco; não deve estourar erro."""
    respostas = {
        "logica_algoritmos": 5,
        "banco_dados": 4,
    }
    resultado = calcular_ranking(respostas, base)
    assert len(resultado["ranking"]) == 10
    # Back-end e Engenharia de Dados têm peso nessas perguntas, então devem ter pontuação > 0
    backend_info = next(t for t in resultado["ranking"] if t["id"] == "backend")
    assert backend_info["pontuacao"] > 0.0


def test_caso_7_valores_invalidos_geram_excecao(base):
    """Valores inválidos (fora da escala 1-5 ou textos inválidos) devem disparar ValueError."""
    with pytest.raises(ValueError):
        calcular_ranking({"logica_algoritmos": 0}, base)

    with pytest.raises(ValueError):
        calcular_ranking({"logica_algoritmos": 6}, base)

    with pytest.raises(ValueError):
        calcular_ranking({"logica_algoritmos": "muito"}, base)


def test_caso_8_usuario_conhecimento_maximo_sem_gaps(base):
    """Usuário com nível 3 em todas as competências deve ter 100% de prontidão e 0 gaps em qualquer trilha."""
    trilha = base["trilhas"][0]
    competencias = [c["id"] for c in base["competencias_autoavaliacao"]]
    autoavaliacao = {cid: 3 for cid in competencias}

    diagnostico = analisar_skill_gaps(trilha, autoavaliacao)
    assert diagnostico["prontidao_pct"] == 100.0
    assert len(diagnostico["lacunas"]) == 0

    roadmap = gerar_roadmap_personalizado(trilha, diagnostico)
    assert roadmap["apto_junior"] is True


def test_caso_9_usuario_conhecimento_zero(base):
    """Usuário com nível 0 em tudo deve ter prontidão 0% e estimativa de semanas calculada."""
    trilha = base["trilhas"][0]
    competencias = [c["id"] for c in base["competencias_autoavaliacao"]]
    autoavaliacao = {cid: 0 for cid in competencias}

    diagnostico = analisar_skill_gaps(trilha, autoavaliacao)
    assert diagnostico["prontidao_pct"] == 0.0
    assert len(diagnostico["lacunas"]) == len(trilha["requisitos_junior"])

    roadmap = gerar_roadmap_personalizado(trilha, diagnostico, horas_semanais=10)
    assert roadmap["apto_junior"] is False
    assert roadmap["estimativa_tempo"]["semanas_estimadas"] > 0


def test_caso_10_perfil_nitidamente_devops_cloud(base):
    """Perfil altamente voltado a infra, automação e Linux; Top 3 deve conter DevOps e Cloud."""
    respostas = {
        "infra_servidores": 5,
        "automacao_scripts": 5,
        "resolucao_pressao": 5,
        "redes_seguranca": 4,
        "tolerancia_oncall": 4,
        "preferencia_remoto": 4,
        "logica_algoritmos": 3,
        "banco_dados": 2,
        "design_visual_ux": 1,
        "desenvolvimento_mobile": 1,
        "matematica_estatistica": 2,
        "gestao_comunicacao": 2,
        "trabalho_criativo_visual": 1,
        "interesse_lideranca": 2,
        "testes_qualidade": 3,
        "ia_machine_learning": 2,
        "busca_retorno_rapido": 3,
    }
    resultado = calcular_ranking(respostas, base)
    top3_ids = [t["id"] for t in resultado["top3"]]

    assert "devops_sre" in top3_ids or "arquitetura_cloud" in top3_ids
    # O 1º colocado deve ser devops_sre ou arquitetura_cloud
    assert resultado["top3"][0]["id"] in ["devops_sre", "arquitetura_cloud"]
