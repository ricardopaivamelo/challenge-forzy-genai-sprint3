# Sprint 3 — Baseline Operacional e Detecção de Anomalias

### Challenge Forzy · FIAP · Manutenção preditiva de motores elétricos

Pipeline semissupervisionado que aprende o comportamento normal dos equipamentos,
detecta desvios em janelas históricas e compara os alertas com o classificador de falhas
conhecidas da Sprint 2.

## Problema

Uma falha industrial pode começar como uma alteração gradual antes de receber um rótulo.
Nesta entrega, comportamento normal é o padrão calibrado para cada motor; uma anomalia é uma
janela cujo score ultrapassa um threshold definido exclusivamente na validação. O alerta
prioriza inspeção, mas não comprova a causa física.

A abordagem é **semissupervisionada**: os rótulos separam períodos confiáveis e avaliam os
resultados, mas não são usados como alvo pelo Isolation Forest nem pelo Autoencoder.

## Dados da Forzy

`data/motor.db` é um SQLite sintético com:

- 20 motores e 30.000 leituras;
- uma leitura por minuto entre 01/01/2026 00:00 e 02/01/2026 00:59;
- sensores de rotação, vibração, temperatura e corrente;
- 26.291 leituras normais e 3.709 leituras com falha rotulada;
- três falhas conhecidas: desbalanceamento, superaquecimento e falha mecânica.

Não existem valores ausentes nem timestamps duplicados por motor. A documentação original
está em `data/BANCO.pdf`.

## Metodologia

1. Separação por motor: treino `[4, 5, 6, 7, 9, 11, 12, 14, 17, 18, 19, 20]`,
   validação `[3, 8, 13]` e teste `[1, 2, 10, 15, 16]` — os mesmos motores de teste da Sprint 2.
2. Calibração individual por mediana/IQR das primeiras 30 leituras.
3. Janelas de 30 minutos, stride de cinco minutos e guarda de 30 minutos ao redor de falhas.
4. Baseline estatístico por desvio robusto.
5. Isolation Forest sobre 24 estatísticas temporais.
6. Autoencoder denso 120–64–16–64–120 treinado para reconstruir janelas normais.
7. Threshold no percentil 99 dos scores normais da validação.
8. Alerta persistente após três janelas consecutivas acima do threshold.

## Resultados no teste

| Modelo | Precision | Recall | F1 | PR-AUC | ROC-AUC | FPR |
|---|---:|---:|---:|---:|---:|---:|
| Baseline estatístico | 0,582 | 0,988 | 0,733 | **0,702** | 0,966 | 0,094 |
| Isolation Forest | 0,579 | 0,942 | 0,717 | 0,665 | 0,957 | 0,091 |
| Autoencoder | **0,605** | 0,924 | 0,731 | 0,537 | 0,947 | **0,080** |
| Random Forest — Sprint 2 | 0,860 | 0,860 | 0,860 | 0,923 | 0,980 | 0,018 |

| Modelo | Eventos detectados | Antecipados | Lead mediano |
|---|---:|---:|---:|
| Baseline estatístico | 23/23 | 12 | +1 min |
| Isolation Forest | 23/23 | 11 | −5 min |
| Autoencoder | 23/23 | 9 | −7 min |
| Random Forest — Sprint 2 | 20/23 | 7 | −7,5 min |

O baseline estatístico obteve o melhor PR-AUC entre os detectores. O Autoencoder produziu
menos falsos positivos entre eles, enquanto o Random Forest continua superior para reconhecer
falhas conhecidas. Isso sustenta uma arquitetura complementar: detecção de anomalias para
triagem e antecipação; classificação supervisionada para sugerir a categoria já conhecida.

Lead positivo significa alerta antes do início rotulado; lead negativo representa atraso.

## Estrutura

```text
├── data/                         motor.db + documentação da base
├── docs/
│   ├── sprint3_report.md         relatório com os 12 entregáveis
│   └── superpowers/              especificação e plano de implementação
├── figuras/                      sete gráficos da Sprint 3 + figuras anteriores
├── models/
│   ├── modelo_anomalias.joblib   detectores, scalers, baselines e thresholds
│   └── anomaly_metrics.json      métricas finais estruturadas
├── notebooks/
│   └── sprint3_anomalias.ipynb   notebook acadêmico executado
├── results/                      scores, eventos e rankings auditáveis
├── src/
│   ├── anomaly_data.py           partições, calibração e janelas
│   ├── anomaly_models.py         baseline, Isolation Forest e Autoencoder
│   ├── anomaly_evaluation.py     métricas, eventos e comparação Sprint 2
│   ├── anomaly_reporting.py      figuras e relatório
│   ├── anomaly_service.py        contrato futuro do agente
│   ├── run_sprint3.py            orquestrador reproduzível
│   └── build_sprint3_notebook.py gerador do notebook
└── tests/                        testes unitários e smoke test integral
```

## Como reproduzir

### 1. Criar o ambiente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Executar os testes

```bash
pytest -q
```

### 3. Recriar todos os artefatos

```bash
python src/run_sprint3.py
```

O comando recria modelo, JSON, CSVs, relatório e sete PNGs sem entrada manual.

### 4. Gerar e executar o notebook

```bash
python src/build_sprint3_notebook.py
jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=1200 notebooks/sprint3_anomalias.ipynb
```

Nenhuma chave, API ou serviço externo é necessário para a Sprint 3.

## Visualizações

- distribuição dos quatro sensores por estado;
- evolução temporal com falhas rotuladas;
- matriz de correlação;
- scores normalizados pelo threshold ao longo do tempo;
- matrizes de confusão dos quatro modelos;
- ranking de motores por alerta/persistência;
- erros de reconstrução por sensor.

## Integração futura com agente

`src/anomaly_service.py` transforma uma detecção em um payload com:

```json
{
  "motor_id": 1,
  "anomaly_score": 0.42,
  "threshold": 0.25,
  "severity": "high",
  "persistent": true,
  "dominant_sensors": ["vibracao_mm_s", "corrente_a"],
  "explanation": "Desvio persistente acima do baseline; recomenda-se inspeção."
}
```

Um agente conversacional poderá reformular esses fatos, mas score, severidade e sensores
continuam sendo produzidos pelo pipeline determinístico.

## Limitações

- dados sintéticos e apenas 25 horas de histórico por motor;
- primeiras 30 leituras assumidas como período saudável de comissionamento;
- thresholds precisam ser recalibrados antes de uso real;
- alerta pré-rótulo pode ser degradação emergente ou falso positivo;
- erro de reconstrução por sensor não é atribuição causal;
- avaliação local não representa validação em produção.

## Checklist dos entregáveis

1. ✅ problema e abordagem semissupervisionada;
2. ✅ documentação da base;
3. ✅ EDA com tabelas e gráficos;
4. ✅ baseline operacional por motor;
5. ✅ preparação temporal sem vazamento;
6. ✅ Isolation Forest e Autoencoder treinados;
7. ✅ métricas de janela e evento;
8. ✅ casos, motores e sensores anômalos;
9. ✅ comparação alinhada com a Sprint 2;
10. ✅ sete visualizações exportadas;
11. ✅ contrato para futuro agente conversacional;
12. ✅ scripts, testes, notebook executado e instruções de reprodução.
