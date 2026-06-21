# Sprint 2 — GenAI · Manutenção Preditiva + Agente com Function Calling
### Challenge Forzy (FIAP) — Digital Twin de motores elétricos industriais

Pipeline completo: **análise exploratória → modelo baseline de classificação de falhas
→ agente conversacional** que diagnostica motores em linguagem natural via *function calling*.

## Problema (entregável 1)
Classificação **multiclasse** do estado do motor a partir de leituras de sensores:
`falha ∈ {0 Normal, 1 Desbalanceamento, 2 Superaquecimento, 3 Falha mecânica}`.
Antecipar a falha é o que permite a manutenção *preditiva*; o foco está nas três classes
de falha (minoritárias), onde está o valor.

## Base de dados (entregável 2)
`data/motor.db` (SQLite) — `motores` (20), `leituras` (30.000 séries de sensores
1/min), `tipos_falha` (4). Sintético, seed fixa. Documentação completa em
`data/BANCO.pdf`. Distribuição: ~87,6% normal · ~12,4% falha.

## Estrutura
```
genai/sprint2/
├── data/              motor.db + BANCO.pdf (dataset de entrada)
├── requisitos/        sprintGenAI_s2.txt (enunciado)
├── src/
│   ├── data_utils.py        carga do motor.db + constantes (fonte de verdade)
│   ├── train.py             treino/avaliação por script (gera o .joblib)
│   ├── build_notebooks.py   gera os notebooks-entregáveis
│   └── agente.py            agente com function calling (OpenAI ou Anthropic)
├── notebooks/
│   ├── analise_exploratoria.ipynb   EDA (entregáveis 3-5)
│   └── treinamento.ipynb            treino, avaliação, erros (entregáveis 6-8)
├── models/
│   ├── modelo_falhas.joblib   modelo serializado (usado pelo agente)
│   └── metrics.json           métricas da última execução
├── figuras/           gráficos exportados da EDA/avaliação
├── requirements.txt
└── .env.example       modelo para a chave do LLM (copiar p/ .env)
```

## Como reproduzir

### Ambiente
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
No **Colab**: suba a pasta (ou clone o repo) e rode `!pip install -r requirements.txt`;
os notebooks usam caminhos relativos a partir de `notebooks/`.

### Notebooks (entregáveis 3–8)
```bash
jupyter notebook notebooks/analise_exploratoria.ipynb
jupyter notebook notebooks/treinamento.ipynb
# ou reexecutar tudo headless:
jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
```

### Agente conversacional (entregável 9)
1. Copie `.env.example` para `.env` e preencha **uma** chave (`OPENAI_API_KEY` ou
   `ANTHROPIC_API_KEY`). O `.env` está no `.gitignore`.
2. Rode:
```bash
python src/agente.py --demo   # 3 cenários: normal, falha clara, ambíguo
python src/agente.py          # chat interativo
```
O usuário descreve as leituras; o LLM chama a tool `prever_falha_motor`, que executa o
modelo de ML e devolve classe + probabilidades; o LLM explica o diagnóstico, os sensores
que pesaram e a incerteza.

## Resultados (baseline)
Random Forest (`class_weight="balanced_subsample"`), split `StratifiedGroupKFold` por
`motor_id` (sem vazamento entre motores). **macro-F1 ≈ 0,80 · acurácia ≈ 0,95.**

| Classe | Recall | F1 |
|---|---|---|
| Normal | 0,98 | 0,98 |
| Desbalanceamento | 0,93 | 0,81 |
| Superaquecimento | 0,72 | 0,70 |
| Falha mecânica | 0,54 | 0,70 |

## Limitações e próximos passos (entregável 8)
- *Falha mecânica* tem o menor recall — confunde-se com desbalanceamento/superaquecimento
  por compartilhar sintomas (vibração/corrente altas).
- O modelo usa **leituras instantâneas** (contrato da tool do agente). A evolução natural
  é **features de janela móvel**, que capturam a *rampa* de deterioração descrita no
  BANCO.md e devem melhorar a separação da falha mecânica.

## Entregáveis (checklist)
1. ✅ Descrição do problema · 2. ✅ Base · 3. ✅ EDA · 4. ✅ Tratamento · 5. ✅ Split ·
6. ✅ Treino · 7. ✅ Avaliação · 8. ✅ Análise de erros · 9. ✅ Agente — demo executada (`docs/demo_agente.md`) ·
10. ✅ Organização e instruções.
