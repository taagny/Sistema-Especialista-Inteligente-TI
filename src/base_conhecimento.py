"""Módulo responsável por carregar e validar a base de conhecimento de regras em JSON."""

import json
from pathlib import Path
from typing import Any, Dict, Set


def obter_caminho_padrao_base() -> Path:
    """Retorna o caminho padrão para o arquivo JSON de regras de carreiras."""
    raiz_projeto = Path(__file__).resolve().parent.parent
    return raiz_projeto / "dados" / "regras_carreiras.json"


def validar_base_conhecimento(base: Dict[str, Any]) -> None:
    """Valida a consistência estrutural e integridade referencial da base de conhecimento.

    Lança ValueError com mensagem detalhada em português caso encontre inconsistências.
    """
    chaves_obrigatorias = [
        "metadados",
        "parametros",
        "niveis_senioridade",
        "competencias_autoavaliacao",
        "perguntas",
        "trilhas",
    ]

    for chave in chaves_obrigatorias:
        if chave not in base:
            raise ValueError(f"A base de conhecimento não contém a seção obrigatória: '{chave}'.")

    # Validação dos parâmetros essenciais
    parametros = base["parametros"]
    for param in ["tolerancia_empate_pct", "tamanho_ranking_destaque"]:
        if param not in parametros:
            raise ValueError(f"Parâmetro essencial ausente na seção 'parametros': '{param}'.")

    # Validação das perguntas
    perguntas = base["perguntas"]
    if not isinstance(perguntas, list) or len(perguntas) < 20:
        raise ValueError(
            f"A lista de perguntas deve conter no mínimo 20 perguntas (foram encontradas {len(perguntas)})."
        )

    ids_perguntas: Set[str] = set()
    for idx, p in enumerate(perguntas):
        for campo in ["id", "texto", "passo", "categoria", "tipo"]:
            if campo not in p:
                raise ValueError(f"Pergunta na posição {idx} não possui o campo obrigatório '{campo}'.")
        pid = p["id"]
        if pid in ids_perguntas:
            raise ValueError(f"ID de pergunta duplicado detectado: '{pid}'.")
        ids_perguntas.add(pid)

    # Validação das competências da autoavaliação
    competencias = base["competencias_autoavaliacao"]
    if not isinstance(competencias, list) or len(competencias) == 0:
        raise ValueError("A seção 'competencias_autoavaliacao' deve conter pelo menos uma competência.")

    ids_competencias: Set[str] = set()
    for comp in competencias:
        if "id" not in comp or "nome" not in comp:
            raise ValueError("Cada competência de autoavaliação deve possuir 'id' e 'nome'.")
        ids_competencias.add(comp["id"])

    # Validação das trilhas
    trilhas = base["trilhas"]
    if not isinstance(trilhas, list) or len(trilhas) != 10:
        raise ValueError(
            f"A base de conhecimento deve conter exatamente 10 trilhas profissionais (foram encontradas {len(trilhas)})."
        )

    ids_trilhas: Set[str] = set()
    condicoes_validas = {"<=", ">=", "==", "<", ">"}

    for t in trilhas:
        for campo in ["id", "nome", "descricao", "pesos", "penalidades", "requisitos_junior", "roadmap"]:
            if campo not in t:
                raise ValueError(f"A trilha '{t.get('id', 'desconhecida')}' não possui o campo '{campo}'.")

        tid = t["id"]
        if tid in ids_trilhas:
            raise ValueError(f"ID de trilha duplicado detectado: '{tid}'.")
        ids_trilhas.add(tid)

        # Checagem dos pesos referenciando perguntas válidas
        pesos = t["pesos"]
        if not isinstance(pesos, dict) or len(pesos) == 0:
            raise ValueError(f"A trilha '{tid}' deve conter um dicionário de pesos não vazio.")

        for pergunta_id, peso in pesos.items():
            if pergunta_id not in ids_perguntas:
                raise ValueError(
                    f"A trilha '{tid}' possui peso para a pergunta '{pergunta_id}', que não existe na lista de perguntas."
                )
            if not isinstance(peso, (int, float)) or peso <= 0:
                raise ValueError(f"O peso da pergunta '{pergunta_id}' na trilha '{tid}' deve ser um número positivo.")

        # Checagem das penalidades
        penalidades = t["penalidades"]
        if not isinstance(penalidades, list):
            raise ValueError(f"O campo 'penalidades' da trilha '{tid}' deve ser uma lista.")

        for pen in penalidades:
            for campo_pen in ["pergunta", "condicao", "valor", "penalidade", "motivo"]:
                if campo_pen not in pen:
                    raise ValueError(
                        f"Uma penalidade na trilha '{tid}' está incompleta (falta '{campo_pen}')."
                    )
            if pen["pergunta"] not in ids_perguntas:
                raise ValueError(
                    f"Penalidade na trilha '{tid}' referencia pergunta inexistente: '{pen['pergunta']}'."
                )
            if pen["condicao"] not in condicoes_validas:
                raise ValueError(
                    f"Condição '{pen['condicao']}' inválida na penalidade da trilha '{tid}'."
                )
            if not isinstance(pen["penalidade"], (int, float)) or pen["penalidade"] <= 0:
                raise ValueError(
                    f"Valor da penalidade na trilha '{tid}' deve ser maior que zero."
                )

        # Checagem dos requisitos de nível júnior
        requisitos = t["requisitos_junior"]
        if not isinstance(requisitos, list) or len(requisitos) == 0:
            raise ValueError(f"A trilha '{tid}' deve possuir pelo menos um requisito de nível júnior.")

        for req in requisitos:
            for campo_req in ["competencia", "nivel_minimo", "peso"]:
                if campo_req not in req:
                    raise ValueError(f"Requisito júnior na trilha '{tid}' não possui '{campo_req}'.")
            if req["competencia"] not in ids_competencias:
                raise ValueError(
                    f"Requisito júnior na trilha '{tid}' referencia competência inexistente: '{req['competencia']}'."
                )
            if req["nivel_minimo"] not in (0, 1, 2, 3):
                raise ValueError(
                    f"Nível mínimo de '{req['competencia']}' na trilha '{tid}' deve ser entre 0 e 3."
                )

        # Checagem do roadmap
        roadmap = t["roadmap"]
        for campo_rdm in ["tecnologias_prioritarias", "certificacoes", "projetos_portfolio"]:
            if campo_rdm not in roadmap:
                raise ValueError(f"O roadmap da trilha '{tid}' não possui a seção '{campo_rdm}'.")


def carregar_base_conhecimento(caminho_arquivo: str | Path | None = None) -> Dict[str, Any]:
    """Carrega o arquivo JSON da base de conhecimento e aplica validação rigorosa.

    Retorna o dicionário com a base validada.
    """
    if caminho_arquivo is None:
        caminho = obter_caminho_padrao_base()
    else:
        caminho = Path(caminho_arquivo)

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo da base de conhecimento não encontrado em: {caminho}")

    with open(caminho, "r", encoding="utf-8") as f:
        try:
            dados = json.load(f)
        except json.JSONDecodeError as erro:
            raise ValueError(f"Erro de sintaxe JSON ao ler '{caminho}': {erro}") from erro

    validar_base_conhecimento(dados)
    return dados
