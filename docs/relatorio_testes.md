# Relatório de Testes de Robustez e Casos Limite

Este documento relata os experimentos e validações realizados sobre o **Motor de Inferência com Pontuação Ponderada** e os módulos auxiliares do sistema especialista **Consultor Avançado de Carreiras em TI**.

Os testes foram executados com `pytest`, contemplando casos normais, limítrofes, ambíguos e entradas com dados parciais ou inválidos.

---

## Metodologia dos Testes

Foram estruturados 10 cenários representativos no arquivo `testes/test_casos_limite.py` com os seguintes objetivos:
1. Validar a sensibilidade a perfis multidisciplinares (detecção de perfil híbrido / empate parcial).
2. Avaliar a estabilidade matemática nos extremos da escala Likert (mínimo de 1 e máximo de 5).
3. Testar a neutralidade do sistema em respostas medianas (escala 3).
4. Verificar o comportamento diante de contradições (ex: alta afinidade visual x baixa afinidade lógica).
5. Assegurar tolerância a respostas parciais (perguntas ignoradas sem causar divisão por zero).
6. Garantir tratamento de exceções amigáveis para valores inválidos.
7. Validar o diagnóstico de lacunas (*skill gaps*) para usuários experientes (sem gaps) e iniciantes absolutos.
8. Confirmar a convergência para trilhas especializadas (ex: DevOps e Cloud).

---

## Resultados dos Casos Limite

### Caso 1: Perfil Ambíguo (Dados & Desenvolvimento Web)
- **Cenário**: Usuário com alta afinidade em lógica (`5`), bancos de dados (`5`), automação (`4`), matemática e machine learning (`4`), e menor afinidade com interfaces visuais (`2`).
- **Top 3 Obtido**:
  1. Ciência de Dados: **86.8%**
  2. Engenharia de Dados: **85.1%**
  3. Desenvolvimento Back-end: **81.1%**
- **Empate Parcial**: Detectado (`True`), com diferença de apenas **1.7%** entre o 1º e o 2º colocado.
- **Análise**: O motor identificou com sucesso o comportamento híbrido e gerou mensagem contextualizada informando a proximidade entre Ciência e Engenharia de Dados.

### Caso 2: Respostas Mínimas (Tudo = 1)
- **Cenário**: Resposta `1` em todas as perguntas Likert.
- **Resultado**: Todas as 10 trilhas registraram compatibilidade final de **0.0%**.
- **Análise**: A normalização `(1 - 1) / 4 = 0.0` funcionou sem gerar divisões por zero ou pontuações negativas, respeitando a barreira inferior `min = 0.0%`.

### Caso 3: Respostas Máximas (Tudo = 5)
- **Cenário**: Resposta `5` em todas as perguntas Likert.
- **Resultado**: Todas as trilhas registraram compatibilidade final de **100.0%**, com **0%** de penalidades aplicadas.
- **Análise**: Nenhuma regra de conflito foi disparada indevidamente e a escala máxima foi atingida uniformemente.

### Caso 4: Respostas Neutras (Tudo = 3)
- **Cenário**: Resposta `3` em todas as perguntas Likert.
- **Resultado**: Todas as 10 trilhas alcançaram exatamente **50.0%** de compatibilidade base.
- **Análise**: A normalização linear manteve a proporcionalidade exata do ponto médio sem penalidades.

### Caso 5: Respostas Contraditórias (Visual Alto x Lógica Baixa)
- **Cenário**: Interesse máximo em design e experiência visual (`5`), porém aversão a lógica e algoritmos (`1`).
- **Resultado**:
  - Front-end & UX permaneceu no topo (**88.6%**).
  - Desenvolvimento Back-end sofreu penalidade severa (**-10%**) por conflito na pergunta `logica_algoritmos <= 2`, caindo para as últimas posições.
- **Análise**: As penalidades lógicas funcionaram como filtro corretivo eficaz, evitando recomendações incoerentes.

### Caso 6: Respostas Parciais (Várias Perguntas em Branco)
- **Cenário**: Usuário preencheu apenas duas perguntas (`logica_algoritmos: 5`, `banco_dados: 4`) e omitiu as demais.
- **Resultado**:
  - Trilhas relacionadas (Back-end e Engenharia de Dados) calcularam pontuação ponderada baseando-se apenas nos pesos das perguntas respondidas.
  - Trilhas sem nenhuma pergunta respondida receberam `0.0%` sem disparar erros.
- **Análise**: O sistema provou ser tolerante à ausência de dados, mantendo a proporcionalidade das respostas fornecidas.

### Caso 7: Entradas Inválidas e Fora da Escala
- **Cenário**: Inserção de valores `0`, `6` ou textos arbitrários (`"muito"`).
- **Resultado**: O motor levantou `ValueError` informativo e consistente, impedindo corrupção no cálculo.
- **Análise**: Proteção essencial contra falhas de integridade nos dados.

### Caso 8: Usuário Experiente (Conhecimento Nível 3 em Tudo)
- **Cenário**: Autoavaliação com nota máxima em todas as competências técnicas.
- **Resultado**:
  - Prontidão para Júnior: **100.0%**.
  - Total de lacunas (*gaps*): **0**.
  - Diagnóstico: Sugestão automática de direcionamento para o nível **Pleno/Sênior**.
- **Análise**: O módulo de roadmap reconheceu a maturidade prévia e adaptou a mensagem de orientação.

### Caso 9: Usuário Iniciante Absoluto (Conhecimento Nível 0 em Tudo)
- **Cenário**: Autoavaliação com nota `0` em todas as competências.
- **Resultado**:
  - Prontidão para Júnior: **0.0%**.
  - Total de lacunas: Lista completa dos requisitos da trilha ordenados por prioridade.
  - Estimativa de tempo: Cálculo realista em semanas com base nas horas semanais informadas.
- **Análise**: Orientação clara e progressiva para estudantes nos primeiros passos.

### Caso 10: Perfil Nítido DevOps & Cloud
- **Cenário**: Afinidade máxima em servidores (`5`), automação (`5`), tolerância a incidentes sob pressão (`5`), redes e segurança (`4`), plantões on-call (`4`), e baixa afinidade com design (`1`).
- **Top 3 Obtido**:
  1. DevOps & Confiabilidade (SRE): **86.4%**
  2. Cibersegurança & Defesa Cibernética: **83.9%**
  3. Arquitetura e Engenharia de Nuvem: **82.9%**
- **Análise**: As três trilhas voltadas à confiabilidade, infraestrutura e segurança dominaram o ranking, comprovando a precisão dos pesos calibrados.

---

## Ajustes e Calibrações Realizados

Durante a rodada inicial de testes de robustez, foram identificadas duas oportunidades de melhoria na modelagem:

1. **Inclusão de Redes em DevOps/SRE**: A trilha de DevOps no JSON continha peso para infraestrutura e servidores, mas não ponderava diretamente a pergunta `redes_seguranca`. Como o ecossistema de contêineres e SRE exige conhecimentos práticos de DNS, roteamento, VPCs e segurança, adicionamos `"redes_seguranca": 7` aos pesos de `devops_sre`.
2. **Calibração de Infraestrutura no Back-end**: O peso de `infra_servidores` na trilha Back-end estava em `6`, muito próximo de trilhas focadas em infra. O valor foi ajustado para `4`, priorizando ainda mais as competências centrais de desenvolvimento (`banco_dados: 10` e `logica_algoritmos: 10`).

Esses ajustes asseguraram diferenciação sem distorcer o cálculo em perfis híbridos.
