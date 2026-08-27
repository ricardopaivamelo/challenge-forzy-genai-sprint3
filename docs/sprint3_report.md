# Relatório técnico — Sprint 3: Baseline e Detecção de Anomalias

## 1. Descrição do problema de anomalias

O objetivo é aprender o comportamento normal de cada motor e sinalizar desvios em janelas de
30 minutos. A abordagem é **semissupervisionada**: rótulos curam treino/validação e avaliam o
resultado, mas não são alvo do Isolation Forest nem do Autoencoder. Alerta indica prioridade
de inspeção, não causa comprovada.

## 2. Descrição dos dados da Forzy

O SQLite contém **30,000 leituras**, **20 motores**, período de
2026-01-01T00:00:00 a 2026-01-02T00:59:00 e frequência de um minuto. Os sensores são rotação, vibração,
temperatura e corrente; `falha` identifica normalidade (0) ou três classes conhecidas (1–3).
Os dados são sintéticos e não validam desempenho industrial real.

## 3. Análise exploratória

As figuras `s3_01` a `s3_03` mostram distribuições, evolução temporal e correlações. As falhas
são progressivas e os níveis normais variam entre motores, justificando baseline individual.
A base não possui valores ausentes nem timestamps duplicados na análise executada.

## 4. Baseline operacional

Cada motor usa mediana e IQR das primeiras 30 leituras. Janelas têm 30 minutos e stride de
cinco minutos. O baseline estatístico usa o maior desvio absoluto médio entre sensores; os
thresholds de percentil 99 da validação são: estatístico **1.2049**,
Isolation Forest **0.5251** e Autoencoder
**0.9513**.

## 5. Preparação dos dados

Treino, validação e teste são separados por motor. O teste preserva `[1, 2, 10, 15, 16]`.
Janelas de treino precisam ser totalmente normais e ficar 30 minutos afastadas de falhas.
Normalização usa somente o período inicial do próprio motor; janelas com lacunas são descartadas.

## 6. Treinamento dos modelos

Foram treinados Isolation Forest com 300 árvores e Autoencoder denso 120–64–16–64–120.
O Autoencoder aprendeu `X → X`; MAE de reconstrução é o score e o erro agregado por sensor
apoia a explicação. O baseline estatístico funciona como referência auditável.

## 7. Avaliação dos resultados

| Modelo | Precision | Recall | F1 | PR-AUC | ROC-AUC | FPR |
|---|---:|---:|---:|---:|---:|---:|
| Baseline estatístico | 0.582 | 0.988 | 0.733 | 0.702 | 0.966 | 0.094 |
| Isolation Forest | 0.579 | 0.942 | 0.717 | 0.665 | 0.957 | 0.091 |
| Autoencoder | 0.605 | 0.924 | 0.731 | 0.537 | 0.947 | 0.080 |
| Random Forest — Sprint 2 | 0.860 | 0.860 | 0.860 | 0.923 | 0.980 | 0.018 |

| Modelo | Eventos detectados | Recall por evento | Antecipados | Lead mediano (min) |
|---|---:|---:|---:|---:|
| Baseline estatístico | 23/23 | 1.000 | 12 | 1.0 |
| Isolation Forest | 23/23 | 1.000 | 11 | -5.0 |
| Autoencoder | 23/23 | 1.000 | 9 | -7.0 |
| Random Forest — Sprint 2 | 20/23 | 0.870 | 7 | -7.5 |

O melhor PR-AUC entre os detectores de anomalia foi **statistical**. O
resultado mostra que complexidade não garante superioridade: o baseline estatístico é uma
referência forte nesta base sintética.

## 8. Análise dos casos anômalos

O motor mais destacado pelo Autoencoder foi o **1**, com taxa de
alerta de **24.7%** e persistência de
**22.0%**. O maior erro médio nos alertas ocorreu em
**Vibração (mm/s)**. Esses erros são
associações do modelo, não atribuição causal da falha.

## 9. Comparação com a Sprint 2

O Random Forest supervisionado reconhece classes conhecidas e obteve F1 binário de
**0.860** nos mesmos endpoints. Os detectores encontram desvios sem
receber a classe de falha e podem alertar antes do rótulo. As abordagens são complementares:
anomalia prioriza investigação; classificação sugere uma categoria conhecida.

## 10. Visualização dos resultados

Sete PNGs mostram sensores, tempo, correlação, scores/thresholds, matrizes de confusão,
ranking de motores e erros por sensor. Os CSVs preservam todos os scores para auditoria.

## 11. Integração futura com agente conversacional

`build_agent_payload()` retorna motor, timestamp, score, threshold, severidade, persistência,
sensores dominantes e explicação. Um LLM futuro poderá reformular esses fatos, mas a decisão e
os números permanecem no pipeline determinístico.

## 12. Código e organização

O comando `python src/run_sprint3.py` recria modelo, métricas, scores, ranking, relatório e
figuras. Testes automatizados cobrem partição, calibração, janelas, thresholds, persistência,
eventos, comparação e contrato conversacional. O notebook executado apresenta todo o fluxo.

## Limitações

- dados sintéticos e apenas 25 horas por motor;
- primeiras 30 leituras assumidas como período de comissionamento saudável;
- threshold calibrado nesta base pode não transferir para produção;
- rótulo atrasado dificulta distinguir antecipação real de falso positivo pré-evento;
- erro por sensor explica reconstrução, não causa física.
