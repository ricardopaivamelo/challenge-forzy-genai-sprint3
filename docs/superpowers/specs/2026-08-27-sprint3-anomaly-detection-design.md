# Sprint 3 — Baseline Operacional e Detecção de Anomalias

## Contexto e objetivo

A Sprint 3 evolui a classificação supervisionada da Sprint 2 para um sistema
semissupervisionado capaz de aprender o comportamento normal dos motores e sinalizar
desvios, inclusive antes de o rótulo de falha aparecer. A entrega deve ser reproduzível,
comparável com o Random Forest anterior e compreensível para manutenção e para uma futura
integração conversacional.

O banco oficial é `data/motor.db`: 20 motores, 30.000 leituras, frequência de uma leitura
por minuto, quatro sensores (`rotacao_rpm`, `vibracao_mm_s`, `temperatura_c`, `corrente_a`)
e rótulos 0–3. Os dados são sintéticos e os rótulos de falha só aparecem após parte da
rampa de degradação; portanto, resultado acadêmico não equivale a validação industrial.

## Decisão de abordagem

A abordagem será **semissupervisionada e híbrida**:

1. baseline estatístico robusto por motor;
2. Isolation Forest como referência clássica não supervisionada;
3. Autoencoder denso como modelo principal, treinado para reconstruir janelas normais;
4. Random Forest da Sprint 2 como comparação supervisionada.

O Autoencoder será implementado com `sklearn.neural_network.MLPRegressor`, treinando
`X -> X`. Isso mantém a entrega leve e reproduzível sem mudar o princípio ensinado pelo
professor: erro de reconstrução alto indica comportamento que o modelo normal não aprendeu.
VAE, LSTM, GAN e dashboard web ficam fora do núcleo porque não acrescentam evidência
suficiente para justificar o risco e o tempo até 31/08/2026.

## Definição operacional

- **Normal:** janela cuja leitura final tem `falha == 0` e cujo padrão é compatível com o
  baseline calibrado para o próprio motor.
- **Anômalo:** janela cujo score supera o threshold calculado exclusivamente na validação.
- **Evento conhecido:** sequência contínua de leituras com `falha > 0`.
- **Alerta persistente:** pelo menos três janelas anômalas consecutivas; com `stride=5`,
  representa aproximadamente 15 minutos de persistência.
- **Antecipação:** alerta persistente emitido até 60 minutos antes do início rotulado de
  um evento.

Anomalia não será descrita como causa comprovada de falha. O sistema aponta desvio e
prioriza inspeção; a classe de falha continua sendo responsabilidade do modelo supervisionado.

## Particionamento e prevenção de vazamento

O teste preservará exatamente os motores da Sprint 2: `[1, 2, 10, 15, 16]`.

- treino: `[4, 5, 6, 7, 9, 11, 12, 14, 17, 18, 19, 20]`;
- validação: `[3, 8, 13]`;
- teste: `[1, 2, 10, 15, 16]`.

Nenhum motor poderá aparecer em mais de uma partição. O threshold e qualquer decisão de
modelo serão definidos na validação; o teste será usado uma única vez para a avaliação final.

Cada motor será calibrado usando somente suas primeiras 30 leituras, por mediana e IQR de
cada sensor. Foi verificado que essas 600 leituras de calibração têm rótulo 0. A normalização
será `(valor - mediana) / max(IQR, epsilon)` e usará apenas o passado do próprio motor.

O treino dos detectores utilizará apenas janelas totalmente normais e afastadas por 30 minutos
antes/depois de qualquer evento rotulado. Os rótulos são usados para curadoria e avaliação,
nunca como alvo do Autoencoder ou do Isolation Forest.

## Janelas e representações

- tamanho: 30 leituras (30 minutos);
- deslocamento: 5 leituras;
- timestamp, rótulo e classe da janela: valores da leitura final;
- sequência do Autoencoder: 30 × 4 valores normalizados, achatados em 120 entradas;
- features do Isolation Forest: média, desvio-padrão, mínimo, máximo, último valor e
  inclinação linear por sensor, totalizando 24 features;
- baseline estatístico: maior média absoluta normalizada entre os quatro sensores na janela.

Janelas nunca atravessarão motores nem lacunas temporais diferentes de um minuto.

## Modelos e thresholds

### Baseline estatístico

Score por janela: máximo, entre sensores, da média do valor absoluto normalizado.
É simples, auditável e estabelece o mínimo que os modelos devem superar.

### Isolation Forest

Treinado nas 24 features das janelas normais de treino com `n_estimators=300`,
`contamination="auto"`, `random_state=42` e `n_jobs=-1`. O score será o negativo de
`score_samples`, de modo que valores maiores sempre representem maior anomalia.

### Autoencoder denso

`MLPRegressor(hidden_layer_sizes=(64, 16, 64), activation="relu", solver="adam",
early_stopping=True, validation_fraction=0.15, n_iter_no_change=15, max_iter=300,
batch_size=64, random_state=42)`. O score será o MAE entre entrada e reconstrução.
A contribuição de cada sensor será o MAE agregado nos 30 passos daquele sensor.

Para cada detector, o threshold será o percentil 99 dos scores de janelas normais da
validação, após excluir a mesma guarda de 30 minutos. Nenhum valor didático do notebook do
professor será copiado para esta base.

## Avaliação

Na leitura final de cada janela, `falha > 0` será o alvo binário de avaliação. Para cada
modelo serão calculados:

- precision, recall, F1 e matriz de confusão no threshold;
- ROC-AUC e PR-AUC usando o score contínuo;
- taxa de falso positivo em janelas normais;
- recall por evento conhecido;
- antecedência ou atraso da primeira detecção persistente por evento;
- ranking de motores por proporção de alertas e score máximo;
- distribuição de sensores dominantes nas anomalias do Autoencoder.

O Random Forest será convertido para comparação binária: `1 - P(normal)` como score e
`classe_predita > 0` como alerta. As métricas usarão os mesmos motores e timestamps finais das
janelas. A comparação separará classificação conhecida, detecção de desvio e antecipação;
macro-F1 multiclasse da Sprint 2 não será comparado diretamente com F1 binário de anomalia.

## Artefatos e visualizações

A entrega conterá:

- pipeline modular e testes automatizados;
- notebook executado `notebooks/sprint3_anomalias.ipynb`;
- modelo serializado `models/modelo_anomalias.joblib`;
- métricas estruturadas `models/anomaly_metrics.json`;
- scores auditáveis `results/anomaly_scores.csv` e ranking por motor;
- gráficos de distribuição, série temporal, correlação, scores/thresholds, matriz de
  confusão, ranking de motores e contribuição de sensores;
- relatório técnico em Markdown e README reescrito para reprodução.

Os gráficos serão PNG estáticos, sem CDN e sem depender de serviço externo.

## Contrato futuro com agente conversacional

O pipeline exporá uma função local que recebe `motor_id` e 30 leituras e retorna:

```json
{
  "motor_id": 1,
  "timestamp": "2026-01-01T12:00:00",
  "anomaly_score": 0.42,
  "threshold": 0.25,
  "severity": "high",
  "persistent": true,
  "dominant_sensors": ["vibracao_mm_s", "corrente_a"],
  "explanation": "Desvio persistente com maior erro em vibração e corrente. Recomenda-se inspeção."
}
```

Severidade será derivada da razão `score / threshold`: abaixo de 1 = normal, de 1 a 1,5 =
atenção e acima de 1,5 = alta. Persistência poderá elevar atenção para alta. A explicação
será determinística; um LLM futuro apenas reformulará os fatos, sem inventar diagnóstico.

## Cobertura dos 12 entregáveis

1. problema e tipo de abordagem: relatório e notebook;
2. documentação dos dados: relatório, README e EDA;
3. análise exploratória: notebook e figuras;
4. baseline operacional: baseline robusto, calibração e thresholds;
5. preparação: testes e pipeline de janelas/normalização;
6. treinamento: Isolation Forest e Autoencoder;
7. avaliação: métricas binárias, ranking e eventos;
8. casos anômalos: relatório, ranking e contribuição por sensor;
9. comparação Sprint 2: mesmas partições e timestamps;
10. visualização: figuras estáticas exportadas;
11. agente futuro: contrato local e proposta arquitetural;
12. código e organização: módulos, testes, notebook executado e instruções.

## Critérios de aceite

- todos os testes passam em ambiente limpo;
- o pipeline completo termina sem entrada manual e recria modelos, CSVs e figuras;
- o notebook executa do início ao fim sem células com erro;
- métricas e números do texto são gerados a partir dos artefatos finais;
- nenhum motor vaza entre treino, validação e teste;
- thresholds não consultam o conjunto de teste;
- README permite reprodução sem segredo ou serviço externo;
- limitações de dados sintéticos, rótulo atrasado e atribuição não causal ficam explícitas.
