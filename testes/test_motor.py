"""Testes unitários do motor de inferência."""

import pytest
from src.base_conhecimento import carregar_base_conhecimento
from src.motor_inferencia import (
    calcular_pontuacao_trilha,
    calcular_ranking,
    normalizar_likert,
    verificar_empates,
)


@pytest.fixture
def base():
    """Carrega a base de conhecimento completa para uso nos testes."""
    return carregar_base_conhecimento()


def test_normalizar_likert_valores_validos():
    """Verifica se a conversão da escala 1-5 para 0.0-1.0 está correta."""
    assert normalizar_likert(1) == 0.0
    assert normalizar_likert(2) == 0.25
    assert normalizar_likert(3) == 0.5
    assert normalizar_likert(4) == 0.75
    assert normalizar_likert(5) == 1.0


def test_normalizar_likert_valores_invalidos():
    """Garante que valores fora da escala ou não numéricos geram erro tratado."""
    with pytest.raises(ValueError):
        normalizar_likert(0)

    with pytest.raises(ValueError):
        normalizar_likert(6)

    with pytest.raises(ValueError):
        normalizar_likert("invalido")

    with pytest.raises(ValueError):
        normalizar_likert(None)


def test_trilha_dominante_frontend(base):
    """Usuário com afinidade máxima em design e criatividade deve ter Front-end em primeiro lugar."""
    respostas = {
        "design_visual_ux": 5,
        "trabalho_criativo_visual": 5,
        "logica_algoritmos": 4,
        "testes_qualidade": 3,
        "busca_retorno_rapido": 5,
        "preferencia_remoto": 5,
        # Áreas não relacionadas baixas
        "desenvolvimento_mobile": 1,
        "infra_servidores": 1,
        "redes_seguranca": 1,
        "matematica_estatistica": 1,
        "ia_machine_learning": 1,
    }

    resultado = calcular_ranking(respostas, base)
    assert len(resultado["ranking"]) == 10
    vencedor = resultado["top3"][0]
    assert vencedor["id"] == "frontend"
    assert vencedor["pontuacao"] > 80.0


def test_aplicacao_de_penalidades(base):
    """Verifica se penalidade lógica é subtraída corretamente quando condição é satisfeita."""
    trilha_frontend = next(t for t in base["trilhas"] if t["id"] == "frontend")

    # Front-end com nota 1 em design deve sofrer penalidade de 12 pontos
    respostas = {
        "design_visual_ux": 1,
        "trabalho_criativo_visual": 5,
        "logica_algoritmos": 5,
    }

    pontuacao = calcular_pontuacao_trilha(trilha_frontend, respostas)
    assert pontuacao["total_penalidades"] >= 12.0
    assert any(p["pergunta"] == "design_visual_ux" for p in pontuacao["penalidades_aplicadas"])
    assert pontuacao["pontuacao"] < pontuacao["pontuacao_base"]


def test_respostas_ausentes_tratadas_com_justica(base):
    """Se o usuário responde apenas metade das perguntas de uma trilha com nota máxima, deve ter 100% base."""
    trilha_backend = next(t for t in base["trilhas"] if t["id"] == "backend")

    respostas_parciais = {
        "logica_algoritmos": 5,
        "banco_dados": 5,
    }

    resultado = calcular_pontuacao_trilha(trilha_backend, respostas_parciais)
    # Ambas as perguntas respondidas tinham nota máxima, então compatibilidade base é 100%
    assert resultado["pontuacao_base"] == 100.0
    assert resultado["total_penalidades"] == 0.0
    assert resultado["pontuacao"] == 100.0


def test_deteccao_de_empate_parcial(base):
    """Verifica detecção de empate técnico quando pontuações são muito próximas."""
    ranking_simulado = [
        {"posicao": 1, "nome": "Engenharia de Dados", "pontuacao": 85.0},
        {"posicao": 2, "nome": "Ciência de Dados", "pontuacao": 83.5},
        {"posicao": 3, "nome": "Back-end", "pontuacao": 70.0},
    ]

    tem_empate, detalhes, msg = verificar_empates(ranking_simulado, tolerancia_pct=3.0)
    assert tem_empate is True
    assert len(detalhes) == 1
    assert "empate técnico" in msg
    assert detalhes[0]["diferenca"] == 1.5


def test_justificativa_gerada_para_top3(base):
    """Garante que as trilhas do Top 3 contêm textos de justificativa bem formados."""
    respostas = {
        "matematica_estatistica": 5,
        "ia_machine_learning": 5,
        "logica_algoritmos": 4,
    }

    resultado = calcular_ranking(respostas, base)
    for trilha in resultado["top3"]:
        assert "justificativa" in trilha
        assert len(trilha["justificativa"]) > 10
