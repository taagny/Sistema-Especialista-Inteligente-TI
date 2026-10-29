# 🧭 Consultor Avançado de Carreiras em TI

Sistema Especialista baseado em regras com tratamento de incerteza, pontuação ponderada, análise de *skill gaps* e recomendação personalizada de roadmap de estudos.

> Trabalho acadêmico da disciplina de Inteligência Artificial, UNIPAC Barbacena, autor: Taagny Augusto

---

## 🎯 Sobre o Projeto

A escolha de uma área de especialização em Tecnologia da Informação costuma gerar muitas dúvidas em estudantes e pessoas em transição de carreira, dada a imensa diversidade de trilhas existentes (desenvolvimento de software, infraestrutura, segurança, dados, gestão).

Neste trabalho, optei por criar um **Sistema Especialista Baseado em Regras** para atuar como um consultor inteligente de carreiras. Diferente de questionários superficiais, o sistema modela o conhecimento de 10 grandes trilhas do mercado de TI, pondera afinidades técnicas e objetivos profissionais, aplica penalidades lógicas a perfis conflitantes, detecta empates parciais (perfis híbridos) e gera um diagnóstico prático de competências faltantes (*skill gaps*) para quem deseja alcançar uma posição de nível **Júnior**.

Por motivos de compatibilidade com versões modernas do Python (3.10+), optei por não utilizar a biblioteca legada *Experta*, implementando um **motor de inferência próprio** em Python puro, com alta legibilidade, separação estrita de responsabilidades e cobertura total por testes unitários.

---

## ✨ Funcionalidades

- **Coleta guiada em formato Wizard (3 passos)**:
  - **Passo 1 (Perfil & Rotina)**: escolaridade, tempo de experiência prévia, horas semanais de estudo e inglês.
  - **Passo 2 (Afinidades Técnicas & Autoavaliação)**: avaliação de interesses em escala Likert (1 a 5) e autoavaliação de conhecimentos práticos em tecnologias-chave (0 a 3).
  - **Passo 3 (Objetivos de Carreira)**: preferências de rotina, modelo de trabalho e expectativas de mercado.
- **Base de conhecimento desacoplada em JSON**: nenhuma pergunta, peso ou regra fica *hardcoded* no código-fonte.
- **Motor de Inferência Ponderado**:
  - Normalização linear da escala Likert (0.0 a 1.0).
  - Soma ponderada por trilha e cálculo percentual relativo às perguntas respondidas.
  - Penalidades condicionais para perfis contraditórios.
  - Detecção inteligente de empates parciais / perfis híbridos com tolerância configurável (3%).
  - Justificativas em linguagem natural explicando o porquê de cada recomendação do Top 3.
- **Diagnóstico de Skill Gaps**:
  - Comparação entre o nível atual do usuário e os requisitos essenciais de nível Júnior da trilha.
  - Cálculo percentual de prontidão técnica para contratação.
  - Priorização automática de lacunas (tamanho do gap $\times$ relevância).
- **Roadmap Personalizado**:
  - Trilha de aprendizado em ordem lógica.
  - Recomendações de certificações reconhecidas (AWS, CompTIA, ISTQB, Azure, Google).
  - Sugestões práticas de projetos para o portfólio no GitHub.
  - Estimativa realista de tempo (horas e semanas) baseada na dedicação informada.
- **Visualização Gráfica Interativa**:
  - Gráfico polar de radar (visão holística das 10 áreas).
  - Gráfico de barras horizontais ordenado e colorido destacando o Top 3.

---

## 🏗️ Estrutura de Pastas

```text
Sistema-Especialista-Inteligente-TI/
├── app.py                      # Interface web completa em Streamlit (wizard)
├── dados/
│   └── regras_carreiras.json   # Base de conhecimento de regras, pesos e roadmaps
├── src/
│   ├── __init__.py
│   ├── base_conhecimento.py    # Carregamento e validação de integridade do JSON
│   ├── motor_inferencia.py     # Motor de inferência (cálculo ponderado, penalidades e ranking)
│   ├── gaps_roadmap.py         # Módulo de análise de skill gaps e cronograma
│   └── graficos.py             # Visualizações interativas com Plotly (radar e barras)
├── testes/
│   ├── test_motor.py           # Testes unitários do motor de inferência
│   ├── test_gaps_roadmap.py    # Testes unitários do módulo de gaps e roadmap
│   └── test_casos_limite.py    # 10 testes de robustez e perfis limítrofes
├── docs/
│   └── relatorio_testes.md     # Relatório analítico detalhado dos casos limite
├── requirements.txt            # Dependências do projeto
├── pytest.ini                  # Configuração de descoberta do pytest
├── .gitignore                  # Arquivos ignorados pelo controle de versão
└── README.md                   # Documentação do projeto
```

---

## 🧠 Como Funciona o Motor de Inferência

O motor de inferência foi projetado como um conjunto de funções puras, facilitando a testabilidade e auditoria dos cálculos.

### 1. Normalização da Escala Likert
Cada resposta $R_i \in [1, 5]$ é mapeada linearmente para o intervalo $[0.0, 1.0]$:

$$N_i = \frac{R_i - 1}{4}$$

- Resposta $1 \rightarrow N = 0.0$ (nenhuma afinidade)
- Resposta $3 \rightarrow N = 0.5$ (afinidade moderada)
- Resposta $5 \rightarrow N = 1.0$ (afinidade total)

### 2. Compatibilidade Base
Para cada uma das 10 trilhas, calcula-se a soma ponderada das perguntas que possuem peso $P_i$ e foram respondidas:

$$C_{base} = \left( \frac{\sum_{i \in \text{respondidas}} (N_i \times P_i)}{\sum_{i \in \text{respondidas}} P_i} \right) \times 100$$

> Caso uma pergunta associada à trilha não seja respondida, ela é desconsiderada de forma justa tanto no numerador quanto no denominador, garantindo que respostas em branco não zerem nem distorçam injustamente a trilha.

### 3. Aplicação de Penalidades Lógicas
Se o usuário assinalar uma resposta incompatível com a exigência estrutural da trilha (ex: nota $\le 2$ em `design_visual_ux` para Front-end, ou nota $\le 2$ em `logica_algoritmos` para Back-end), o sistema aplica uma penalidade percentual direta:

$$P_{final} = \max\left(0.0, \min\left(100.0, C_{base} - \sum \text{Penalidades}\right)\right)$$

### 4. Exemplo Numérico Simples

Imagine a trilha de **Desenvolvimento Back-end**, cujos pesos principais são:
- `logica_algoritmos`: peso 10
- `banco_dados`: peso 10
- `automacao_scripts`: peso 6

Se o usuário responder:
- `logica_algoritmos`: 5 $\rightarrow N = 1.0$
- `banco_dados`: 4 $\rightarrow N = 0.75$
- `automacao_scripts`: 3 $\rightarrow N = 0.5$

Cálculo da pontuação bruta:
$$(1.0 \times 10) + (0.75 \times 10) + (0.5 \times 6) = 10 + 7.5 + 3 = 20.5$$

Peso máximo possível:
$$10 + 10 + 6 = 26$$

Compatibilidade base:
$$C_{base} = \left(\frac{20.5}{26}\right) \times 100 \approx 78.8\%$$

Como nenhuma resposta ativou regras de conflito (lógica foi 5 e banco foi 4), a penalidade é zero e a compatibilidade final resulta em **78.8%**.

### 5. Detecção de Empate Parcial (Perfil Híbrido)
Se a diferença entre a pontuação de duas trilhas consecutivas nas primeiras posições for menor ou igual à tolerância estipulada (`tolerancia_empate_pct = 3.0%`), o sistema sinaliza um **empate técnico** e destaca que o estudante possui um perfil híbrido entre ambas as áreas.

---

## 📊 Estrutura da Base de Conhecimento (`regras_carreiras.json`)

O arquivo JSON centraliza todo o domínio e é validado na inicialização pela função `validar_base_conhecimento`:

1. `metadados`: versão, títulos e rótulos das escalas Likert (1 a 5) e conhecimento prático (0 a 3).
2. `parametros`: tolerância para empate (3.0%), tamanho do ranking de destaque (3) e estimativa de horas por nível de gap (40h).
3. `perguntas`: 22 perguntas divididas entre perfil pessoal, afinidades técnicas e objetivos de carreira.
4. `competencias_autoavaliacao`: 10 competências essenciais (Python, SQL, Git, Linux, Docker, Nuvem, APIs REST, etc.).
5. `trilhas`: 10 trilhas modeladas (*Back-end, Front-end/UX, Ciência de Dados, Engenharia de Dados, Cibersegurança, DevOps/SRE, Arquitetura Cloud, Mobile, QA/Qualidade, Gestão de Produtos*), cada uma com:
   - `pesos`: mapeamento de relevância de cada pergunta.
   - `penalidades`: regras de conflito com motivo e valor de redução.
   - `requisitos_junior`: competências obrigatórias com nível mínimo (0 a 3) e peso.
   - `roadmap`: lista de tecnologias prioritárias, certificações oficiais e projetos para portfólio.

---

## 🚀 Como Instalar e Rodar

### Pré-requisitos
- Python 3.10 ou superior instalado.
- Git instalado.

### 1. Clonar o Repositório
```bash
git clone https://github.com/taagny/Sistema-Especialista-Inteligente-TI.git
cd Sistema-Especialista-Inteligente-TI
```

### 2. Criar e Ativar o Ambiente Virtual
- **No Windows (PowerShell)**:
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
- **No Linux / macOS**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a Aplicação Web
```bash
streamlit run app.py
```
A aplicação abrirá automaticamente no navegador no endereço `http://localhost:8501`.

### 5. Executar a Suíte de Testes
```bash
pytest -v
```

---

## 🧪 Relatório de Testes de Robustez

A suíte conta com **21 testes automatizados**, cobrindo o motor de cálculo, a análise de lacunas e 10 cenários limite (respostas mínimas, máximas, neutras, contraditórias, ambíguas, entradas parciais e valores inválidos).

Para conferir a análise detalhada e os percentuais obtidos em cada caso, consulte o documento:
👉 [Relatório de Testes de Robustez](docs/relatorio_testes.md)

---

## 🔮 Limitações Conhecidas e Melhorias Futuras

- **Aprofundamento de soft skills**: embora o sistema contemple perguntas sobre liderança e comunicação, o foco predominante é técnico; no futuro, uma bateria complementar de perguntas comportamentais pode refinar o perfil para cargos de liderança.
- **Integração com vagas reais**: uma evolução interessante seria conectar a aplicação a APIs públicas de vagas (como LinkedIn Jobs ou GitHub Jobs) para correlacionar os gaps do aluno com os requisitos das vagas abertas na sua região.
- **Exportação em PDF**: permitir que o estudante baixe seu roadmap e diagnóstico em um documento PDF formatado.
