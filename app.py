"""Aplicação Web em Streamlit - Consultor Avançado de Carreiras em TI."""

from typing import Any, Dict
import pandas as pd
import streamlit as st

from src.base_conhecimento import carregar_base_conhecimento
from src.gaps_roadmap import analisar_skill_gaps, gerar_roadmap_personalizado
from src.graficos import criar_grafico_barras, criar_grafico_radar
from src.motor_inferencia import calcular_ranking


@st.cache_data
def obter_base_carregada() -> Dict[str, Any]:
    """Carrega e valida o arquivo JSON uma única vez em cache."""
    return carregar_base_conhecimento()


def inicializar_estado(base: Dict[str, Any]) -> None:
    """Configura as variáveis de sessão padrão se ainda não existirem."""
    if "passo_atual" not in st.session_state:
        st.session_state.passo_atual = 1

    if "respostas" not in st.session_state:
        st.session_state.respostas = {}

    if "autoavaliacao" not in st.session_state:
        st.session_state.autoavaliacao = {}

    if "resultado" not in st.session_state:
        st.session_state.resultado = None


def reiniciar_teste() -> None:
    """Limpa as respostas e retorna para o primeiro passo."""
    st.session_state.passo_atual = 1
    st.session_state.respostas = {}
    st.session_state.autoavaliacao = {}
    st.session_state.resultado = None
    st.rerun()


def renderizar_passo_1(base: Dict[str, Any]) -> None:
    """Passo 1: Coleta de informações sobre perfil acadêmico e rotina."""
    st.subheader("Passo 1 de 3: Perfil Pessoal & Rotina")
    st.write(
        "Para iniciarmos, conte-nos um pouco sobre seu momento de formação e tempo disponível para estudo."
    )

    perguntas_passo1 = [p for p in base["perguntas"] if p.get("passo") == 1]

    for p in perguntas_passo1:
        pid = p["id"]
        tipo = p.get("tipo")
        texto = p["texto"]

        if tipo == "escolha_unica":
            opcoes = p.get("opcoes", [])
            idx_padrao = 0
            if pid in st.session_state.respostas and st.session_state.respostas[pid] in opcoes:
                idx_padrao = opcoes.index(st.session_state.respostas[pid])

            resp = st.selectbox(texto, opcoes, index=idx_padrao, key=f"p1_{pid}")
            st.session_state.respostas[pid] = resp

        elif tipo == "numerico":
            minimo = p.get("minimo", 2)
            maximo = p.get("maximo", 50)
            padrao = p.get("padrao", 10)
            valor_atual = st.session_state.respostas.get(pid, padrao)

            resp = st.slider(
                texto,
                min_value=minimo,
                max_value=maximo,
                value=int(valor_atual),
                step=1,
                help="Esse valor será usado para estimar o cronograma de estudos no roadmap.",
                key=f"p1_{pid}",
            )
            st.session_state.respostas[pid] = resp

    st.write("")
    col_vazia, col_avancar = st.columns([4, 1])
    with col_avancar:
        if st.button("Avançar ➡️", use_container_width=True, type="primary"):
            st.session_state.passo_atual = 2
            st.rerun()


def renderizar_passo_2(base: Dict[str, Any]) -> None:
    """Passo 2: Afinidades técnicas com escala Likert e autoavaliação prática."""
    st.subheader("Passo 2 de 3: Afinidades Técnicas & Autoavaliação")
    st.write(
        "Indique o quanto você se identifica com cada tema técnico e, em seguida, avalie seus conhecimentos atuais."
    )

    escala_likert = base["metadados"]["escala_likert"]
    rotulos_likert = {int(k): f"{k} - {v}" for k, v in escala_likert.items()}

    perguntas_passo2 = [p for p in base["perguntas"] if p.get("passo") == 2]

    st.markdown("#### Afinidades Técnicas")
    for p in perguntas_passo2:
        pid = p["id"]
        texto = p["texto"]
        valor_salvo = st.session_state.respostas.get(pid, 3)

        escolha = st.select_slider(
            texto,
            options=[1, 2, 3, 4, 5],
            value=int(valor_salvo),
            format_func=lambda x: rotulos_likert.get(x, str(x)),
            key=f"p2_{pid}",
        )
        st.session_state.respostas[pid] = escolha

    st.write("")
    st.markdown("---")
    st.markdown("#### Autoavaliação de Conhecimentos Práticos")
    st.caption(
        "Essas respostas alimentam a análise de lacunas (skill gaps) e a geração do roadmap para nível Júnior."
    )

    escala_conhecimento = base["metadados"]["escala_conhecimento"]
    rotulos_conhecimento = {int(k): f"{k} - {v}" for k, v in escala_conhecimento.items()}

    competencias = base.get("competencias_autoavaliacao", [])
    cols = st.columns(2)

    for idx, comp in enumerate(competencias):
        cid = comp["id"]
        coluna = cols[idx % 2]
        val_salvo = st.session_state.autoavaliacao.get(cid, 0)

        with coluna:
            st.markdown(f"**{comp['nome']}**")
            st.caption(comp.get("descricao", ""))
            escolha = st.select_slider(
                f"Seu nível em {comp['nome']}:",
                options=[0, 1, 2, 3],
                value=int(val_salvo),
                format_func=lambda x: rotulos_conhecimento.get(x, str(x)),
                label_visibility="collapsed",
                key=f"comp_{cid}",
            )
            st.session_state.autoavaliacao[cid] = escolha
            st.write("")

    col_voltar, col_vazio, col_avancar = st.columns([1, 3, 1])
    with col_voltar:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.session_state.passo_atual = 1
            st.rerun()
    with col_avancar:
        if st.button("Avançar ➡️", use_container_width=True, type="primary"):
            st.session_state.passo_atual = 3
            st.rerun()


def renderizar_passo_3(base: Dict[str, Any]) -> None:
    """Passo 3: Preferências e objetivos de carreira."""
    st.subheader("Passo 3 de 3: Objetivos de Carreira & Trabalho")
    st.write("Para finalizar, indique suas preferências quanto ao ambiente e estilo de trabalho.")

    escala_likert = base["metadados"]["escala_likert"]
    rotulos_likert = {int(k): f"{k} - {v}" for k, v in escala_likert.items()}

    perguntas_passo3 = [p for p in base["perguntas"] if p.get("passo") == 3]

    for p in perguntas_passo3:
        pid = p["id"]
        texto = p["texto"]
        valor_salvo = st.session_state.respostas.get(pid, 3)

        escolha = st.select_slider(
            texto,
            options=[1, 2, 3, 4, 5],
            value=int(valor_salvo),
            format_func=lambda x: rotulos_likert.get(x, str(x)),
            key=f"p3_{pid}",
        )
        st.session_state.respostas[pid] = escolha

    st.write("")
    col_voltar, col_vazio, col_calcular = st.columns([1, 2, 2])
    with col_voltar:
        if st.button("⬅️ Voltar", use_container_width=True):
            st.session_state.passo_atual = 2
            st.rerun()
    with col_calcular:
        if st.button("🎯 Calcular Recomendações", use_container_width=True, type="primary"):
            resultado = calcular_ranking(st.session_state.respostas, base)
            st.session_state.resultado = resultado
            st.session_state.passo_atual = 4
            st.rerun()


def renderizar_resultado(base: Dict[str, Any]) -> None:
    """Passo 4: Tela de resultados com gráficos, ranking, gaps e roadmap."""
    resultado = st.session_state.resultado
    if not resultado:
        st.warning("Nenhum resultado calculado. Retorne ao início.")
        if st.button("Voltar ao início"):
            reiniciar_teste()
        return

    st.success("Análise de compatibilidade concluída com sucesso!")

    # Alerta em caso de empate parcial / perfil híbrido
    if resultado.get("empate_parcial"):
        st.info(f"💡 **Perfil Híbrido Detectado:** {resultado.get('mensagem_empate')}")

    # Exibição das métricas do Top 3
    top3 = resultado.get("top3", [])
    st.markdown("### 🏆 Suas Trilhas Mais Compatíveis")

    cols_metricas = st.columns(3)
    medalhas = ["🥇 1º Lugar", "🥈 2º Lugar", "🥉 3º Lugar"]

    for idx, item in enumerate(top3):
        with cols_metricas[idx]:
            st.metric(
                label=medalhas[idx],
                value=item["nome"],
                delta=f"{item['pontuacao']}% de aderência",
            )
            st.caption(item["descricao"])

    st.write("")
    st.markdown("---")

    # Visualização gráfica: Radar e Barras
    st.markdown("### 📊 Visão Geral das 10 Trilhas de TI")
    col_radar, col_barras = st.columns(2)

    with col_radar:
        st.markdown("**Mapa de Compatibilidade (Radar)**")
        fig_radar = criar_grafico_radar(resultado["ranking"])
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_barras:
        st.markdown("**Comparativo em Barras Horizontais**")
        fig_barras = criar_grafico_barras(resultado["ranking"])
        st.plotly_chart(fig_barras, use_container_width=True)

    # Justificativas do motor de inferência
    st.markdown("### 🔍 Por que essas trilhas foram recomendadas?")
    for item in top3:
        with st.expander(f"Justificativa para **{item['nome']}** ({item['pontuacao']}%)"):
            st.write(item["justificativa"])
            if item.get("penalidades_aplicadas"):
                st.markdown("**Regras de conflito ativadas:**")
                for pen in item["penalidades_aplicadas"]:
                    st.caption(f"- Subtraídos {pen['penalidade']:.0f}%: {pen['motivo']}")

    # Tabela com ranking completo
    with st.expander("Ver tabela do ranking completo (10 trilhas)"):
        dados_tabela = [
            {
                "Posição": f"{t['posicao']}º",
                "Trilha": t["nome"],
                "Compatibilidade Final": f"{t['pontuacao']}%",
                "Pontuação Base": f"{t['pontuacao_base']}%",
                "Penalidades": f"-{t['total_penalidades']}%" if t["total_penalidades"] > 0 else "0%",
            }
            for t in resultado["ranking"]
        ]
        df_ranking = pd.DataFrame(dados_tabela)
        st.dataframe(df_ranking, hide_index=True, use_container_width=True)

    st.write("")
    st.markdown("---")

    # Seção de Skill Gaps e Roadmap
    st.markdown("### 🗺️ Diagnóstico de Skill Gaps & Roadmap Júnior")
    st.write(
        "Selecione uma das suas trilhas em destaque para analisar as lacunas técnicas em relação ao nível Júnior e gerar o plano de estudos."
    )

    opcoes_trilhas = {t["nome"]: t["id"] for t in top3}
    nome_selecionado = st.selectbox(
        "Trilha para detalhamento:",
        list(opcoes_trilhas.keys()),
        index=0,
    )
    trilha_id_selecionada = opcoes_trilhas[nome_selecionado]
    trilha_obj = next(t for t in base["trilhas"] if t["id"] == trilha_id_selecionada)

    mapa_competencias = {c["id"]: c for c in base.get("competencias_autoavaliacao", [])}
    diagnostico = analisar_skill_gaps(trilha_obj, st.session_state.autoavaliacao, mapa_competencias)

    horas_semanais = int(st.session_state.respostas.get("horas_semanais", 10))
    horas_por_gap = int(base.get("parametros", {}).get("horas_estimadas_por_nivel_gap", 40))
    roadmap = gerar_roadmap_personalizado(trilha_obj, diagnostico, horas_semanais, horas_por_gap)

    # Indicador de Prontidão
    col_pront1, col_pront2 = st.columns([3, 1])
    with col_pront1:
        st.markdown(f"**Prontidão para contratação como Júnior em {trilha_obj['nome']}:**")
        st.progress(diagnostico["prontidao_pct"] / 100.0)
    with col_pront2:
        st.metric("Prontidão Atual", f"{diagnostico['prontidao_pct']}%")

    st.info(roadmap["mensagem_status"])

    # Tabela de Lacunas
    if diagnostico["lacunas"]:
        st.markdown("#### 🎯 Competências Prioritárias para Desenvolver")
        tabela_gaps = [
            {
                "Competência": gap["nome"],
                "Seu Nível Atual": f"{gap['nivel_atual']}/3",
                "Nível Exigido (Júnior)": f"{gap['nivel_exigido']}/3",
                "Tamanho da Lacuna": f"{gap['lacuna']} nível(is)",
                "Importância na Trilha": f"Peso {gap['peso']:.0f}",
            }
            for gap in diagnostico["lacunas"]
        ]
        st.dataframe(pd.DataFrame(tabela_gaps), hide_index=True, use_container_width=True)

    # Abas do Roadmap
    st.markdown("#### 🚀 Plano de Ação Personalizado")
    tab_tecnologias, tab_certificacoes, tab_projetos = st.tabs(
        ["📚 Tecnologias para Estudar", "🏅 Certificações Sugeridas", "💻 Projetos para GitHub"]
    )

    with tab_tecnologias:
        st.markdown("**Ordem recomendada de aprendizado técnico:**")
        for idx, tec in enumerate(roadmap["tecnologias_prioritarias"], start=1):
            st.markdown(f"{idx}. {tec}")

        st.caption(f"⏱️ {roadmap['estimativa_tempo']['texto_estimativa']}")

    with tab_certificacoes:
        st.markdown("**Certificações que agregam valor real ao currículo:**")
        for cert in roadmap["certificacoes_recomendadas"]:
            with st.container(border=True):
                st.markdown(f"**{cert['nome']}**")
                st.caption(f"Emissor: {cert.get('emissor', 'Oficial')}")
                st.write(cert.get("descricao", ""))

    with tab_projetos:
        st.markdown("**Ideias práticas para demonstrar domínio no GitHub:**")
        for proj in roadmap["projetos_portfolio"]:
            with st.container(border=True):
                st.markdown(f"**{proj['titulo']}**")
                st.write(proj["descricao"])
                st.caption(f"Tecnologias recomendadas: {', '.join(proj.get('tecnologias', []))}")

    st.write("")
    st.markdown("---")
    if st.button("🔄 Refazer Avaliação", type="secondary"):
        reiniciar_teste()


def main() -> None:
    """Ponto de entrada da aplicação."""
    st.set_page_config(
        page_title="Consultor Avançado de Carreiras em TI",
        page_icon="🧭",
        layout="wide",
    )

    st.title("🧭 Consultor Avançado de Carreiras em TI")
    st.caption(
        "Sistema Especialista baseado em regras com pontuação ponderada e análise de gaps de competências."
    )

    base = obter_base_carregada()
    inicializar_estado(base)

    # Indicador de progresso do wizard
    passos_total = 4
    progresso = (st.session_state.passo_atual - 1) / (passos_total - 1)
    st.progress(progresso)

    if st.session_state.passo_atual == 1:
        renderizar_passo_1(base)
    elif st.session_state.passo_atual == 2:
        renderizar_passo_2(base)
    elif st.session_state.passo_atual == 3:
        renderizar_passo_3(base)
    elif st.session_state.passo_atual == 4:
        renderizar_passo_4 = renderizar_resultado
        renderizar_passo_4(base)


if __name__ == "__main__":
    main()
