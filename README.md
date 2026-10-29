# Consultor Avançado de Carreiras em TI

Sistema especialista baseado em regras com tratamento de incerteza e pontuação ponderada, desenvolvido para a disciplina de Inteligência Artificial do curso de Ciência da Computação na UNIPAC Barbacena.

O objetivo do sistema é apoiar estudantes e pessoas em transição de carreira a identificarem as trilhas de TI mais compatíveis com seu perfil, interesses técnicos e objetivos profissionais, além de diagnosticar lacunas de competências (*skill gaps*) e gerar um roadmap prático para o nível Júnior.

## Estrutura do Projeto

- `dados/`: base de conhecimento com regras, pesos, penalidades e roadmaps em JSON.
- `src/`: módulos do sistema especialista (validação da base, motor de inferência, gaps/roadmap e gráficos).
- `testes/`: suíte de testes automatizados com pytest.
- `docs/`: relatórios de testes e documentações complementares.
- `app.py`: interface gráfica web desenvolvida em Streamlit.

## Instalação e Execução

1. Criar e ativar o ambiente virtual:
   ```bash
   python -m venv .venv
   # No Windows:
   .venv\Scripts\activate
   # No Linux/Mac:
   source .venv/bin/activate
   ```

2. Instalar as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Rodar a aplicação:
   ```bash
   streamlit run app.py
   ```

4. Executar os testes:
   ```bash
   pytest
   ```
