"""Geração de gráficos interativos com Plotly para visualização dos resultados."""

from typing import Any, Dict, List
import plotly.graph_objects as go


def criar_grafico_radar(ranking: List[Dict[str, Any]]) -> go.Figure:
    """Gera um gráfico polar (radar) com a compatibilidade percentual das 10 trilhas."""
    # Para fechar o radar, repetimos o primeiro ponto no final
    nomes = [item["nome"] for item in ranking]
    pontuacoes = [item["pontuacao"] for item in ranking]

    nomes_fechados = nomes + [nomes[0]]
    pontuacoes_fechadas = pontuacoes + [pontuacoes[0]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=pontuacoes_fechadas,
            theta=nomes_fechados,
            fill="toself",
            fillcolor="rgba(33, 150, 243, 0.25)",
            line=dict(color="#1976D2", width=2),
            marker=dict(size=6, color="#0D47A1"),
            name="Compatibilidade (%)",
            hovertemplate="<b>%{theta}</b><br>Compatibilidade: %{r:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10),
                ticksuffix="%",
                gridcolor="rgba(200, 200, 200, 0.4)",
            ),
            angularaxis=dict(
                tickfont=dict(size=11),
                direction="clockwise",
            ),
        ),
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=450,
    )

    return fig


def criar_grafico_barras(ranking: List[Dict[str, Any]]) -> go.Figure:
    """Gera um gráfico de barras horizontais ordenado com as 10 trilhas."""
    # Inverte a ordem para que o 1º lugar fique no topo do gráfico horizontal
    ranking_invertido = list(reversed(ranking))
    nomes = [item["nome"] for item in ranking_invertido]
    pontuacoes = [item["pontuacao"] for item in ranking_invertido]
    posicoes = [item["posicao"] for item in ranking_invertido]

    # Cores diferenciadas: azul escuro para o Top 3, azul suave para as demais
    cores = [
        "#1E88E5" if pos <= 3 else "#90CAF9"
        for pos in posicoes
    ]

    fig = go.Figure(
        go.Bar(
            x=pontuacoes,
            y=nomes,
            orientation="h",
            marker=dict(color=cores, line=dict(color="#1565C0", width=1)),
            text=[f"{p:.1f}%" for p in pontuacoes],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Pontuação: %{x:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        xaxis=dict(
            title="Compatibilidade (%)",
            range=[0, 105],
            ticksuffix="%",
            gridcolor="rgba(200, 200, 200, 0.4)",
        ),
        yaxis=dict(
            autorange=True,
            tickfont=dict(size=11),
        ),
        margin=dict(l=10, r=30, t=20, b=40),
        height=420,
    )

    return fig
