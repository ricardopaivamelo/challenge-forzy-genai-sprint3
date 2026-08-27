# Sprint 3 Anomaly Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar um pipeline reproduzível que constrói o baseline operacional dos motores, treina Isolation Forest e Autoencoder, avalia anomalias e compara os resultados com a Sprint 2.

**Architecture:** Os dados SQLite são normalizados pelo baseline de calibração de cada motor e convertidos em janelas temporais. Módulos separados cuidam de preparação, modelos, avaliação e artefatos; um script orquestrador e um notebook executado apresentam a entrega acadêmica.

**Tech Stack:** Python 3.12, pandas, NumPy, scikit-learn, SciPy, Matplotlib, Seaborn, joblib, pytest, Jupyter/nbconvert.

**Spec:** `docs/superpowers/specs/2026-08-27-sprint3-anomaly-detection-design.md`

## Global Constraints

- Prazo da entrega: 31/08/2026.
- Teste fixo: motores `[1, 2, 10, 15, 16]`.
- Validação fixa: motores `[3, 8, 13]`.
- Janela: 30 leituras; stride: 5; guarda: 30 minutos; calibração: 30 leituras.
- Threshold: percentil 99 das janelas normais e limpas da validação.
- Nenhum threshold ou hiperparâmetro pode consultar os motores de teste.
- Nenhum serviço externo, segredo, push ou deploy é necessário.
- Dados sintéticos e contribuições por sensor não causais devem ser declarados.

---

### Task 1: Contratos de dados, partições e janelas

**Files:**
- Create: `src/__init__.py`
- Create: `src/anomaly_data.py`
- Create: `tests/test_anomaly_data.py`
- Create: `pyproject.toml`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: `src.data_utils.load_leituras()` e `src.data_utils.FEATURES`.
- Produces: `SplitConfig`, `WindowConfig`, `PreparedWindows`, `assign_partition()`, `fit_motor_baselines()`, `normalize_by_motor()`, `build_windows()` e `prepare_windows()`.

- [ ] **Step 1: configurar pytest e escrever os testes de partição**

```python
def test_assign_partition_keeps_motors_disjoint(sample_readings):
    assigned = assign_partition(sample_readings)
    groups = assigned.groupby("motor_id")["partition"].nunique()
    assert groups.eq(1).all()
    assert set(assigned.query("partition == 'test'").motor_id) == {1, 2, 10, 15, 16}
```

- [ ] **Step 2: executar o RED**

Run: `.venv/bin/pytest tests/test_anomaly_data.py -q`

Expected: FAIL por ausência de `src.anomaly_data`.

- [ ] **Step 3: implementar partições e calibração robusta**

```python
@dataclass(frozen=True)
class SplitConfig:
    validation_motors: tuple[int, ...] = (3, 8, 13)
    test_motors: tuple[int, ...] = (1, 2, 10, 15, 16)

def fit_motor_baselines(df, calibration_size=30, epsilon=1e-6):
    calibration = df.sort_values(["motor_id", "timestamp"]).groupby("motor_id").head(calibration_size)
    medians = calibration.groupby("motor_id")[FEATURES].median()
    iqrs = calibration.groupby("motor_id")[FEATURES].quantile(.75) - calibration.groupby("motor_id")[FEATURES].quantile(.25)
    return {"median": medians, "iqr": iqrs.clip(lower=epsilon)}
```

- [ ] **Step 4: escrever os testes de normalização, guarda e janela**

Os testes devem provar: mediana de calibração próxima de zero; IQR zero protegido por `epsilon`; nenhuma janela atravessa motor/lacuna; sequência com shape `(n, 30, 4)`; resumo com 24 features; janela de treino só é elegível quando todas as leituras estão normais e fora da guarda.

- [ ] **Step 5: executar o RED das janelas**

Run: `.venv/bin/pytest tests/test_anomaly_data.py -q`

Expected: FAIL nas funções ainda ausentes.

- [ ] **Step 6: implementar preparação mínima até os testes passarem**

`PreparedWindows` deve guardar `sequences`, `summaries`, `metadata`, `feature_names`, `baselines` e `config`. A inclinação de cada sensor será calculada por regressão linear contra `np.arange(30)`.

- [ ] **Step 7: executar GREEN e suíte completa**

Run: `.venv/bin/pytest -q`

Expected: todos os testes passam.

- [ ] **Step 8: commit**

```bash
git add pyproject.toml requirements.txt src/__init__.py src/anomaly_data.py tests/test_anomaly_data.py
git commit -m "feat: add leak-safe anomaly window preparation"
```

---

### Task 2: Baseline estatístico, Isolation Forest e Autoencoder

**Files:**
- Create: `src/anomaly_models.py`
- Create: `tests/test_anomaly_models.py`

**Interfaces:**
- Consumes: `PreparedWindows` da Task 1.
- Produces: `AnomalyModelBundle`, `statistical_scores()`, `fit_anomaly_models()`, `score_anomaly_models()`, `apply_threshold_and_persistence()`.

- [ ] **Step 1: escrever testes de orientação dos scores e threshold**

```python
def test_statistical_score_increases_for_large_sensor_deviation():
    normal = np.zeros((1, 30, 4))
    anomaly = normal.copy()
    anomaly[:, :, 1] = 8.0
    assert statistical_scores(anomaly)[0] > statistical_scores(normal)[0]

def test_threshold_uses_only_validation_normals(prepared_windows):
    bundle = fit_anomaly_models(prepared_windows)
    assert bundle.threshold_source == "validation_normal_guard_clean"
```

- [ ] **Step 2: executar RED**

Run: `.venv/bin/pytest tests/test_anomaly_models.py -q`

Expected: FAIL por módulo ausente.

- [ ] **Step 3: implementar os três detectores**

```python
isolation_forest = IsolationForest(
    n_estimators=300, contamination="auto", random_state=42, n_jobs=-1
)
autoencoder = MLPRegressor(
    hidden_layer_sizes=(64, 16, 64), activation="relu", solver="adam",
    early_stopping=True, validation_fraction=.15, n_iter_no_change=15,
    max_iter=300, batch_size=64, random_state=42,
)
autoencoder.fit(X_train_scaled, X_train_scaled)
```

Cada threshold será `np.quantile(validation_normal_scores, .99)`. O bundle guardará scalers, modelos, thresholds, baselines, configurações e nomes de features.

- [ ] **Step 4: testar contribuição por sensor e persistência**

Provar que `sensor_errors` tem quatro colunas na ordem de `FEATURES` e que apenas a terceira janela consecutiva acima do threshold recebe `persistent=True`.

- [ ] **Step 5: executar GREEN e suíte completa**

Run: `.venv/bin/pytest -q`

Expected: todos os testes passam sem consultar partição de teste durante `fit`.

- [ ] **Step 6: commit**

```bash
git add src/anomaly_models.py tests/test_anomaly_models.py
git commit -m "feat: train hybrid anomaly detectors"
```

---

### Task 3: Métricas, eventos e comparação com Sprint 2

**Files:**
- Create: `src/anomaly_evaluation.py`
- Create: `tests/test_anomaly_evaluation.py`

**Interfaces:**
- Consumes: metadata e scores da Task 2, `models/modelo_falhas.joblib` e leituras originais.
- Produces: `binary_metrics()`, `extract_fault_events()`, `evaluate_events()`, `compare_sprint2()`, `build_motor_ranking()` e `build_sensor_ranking()`.

- [ ] **Step 1: escrever testes com métricas calculadas manualmente**

```python
def test_binary_metrics_match_hand_checked_confusion_matrix():
    result = binary_metrics(
        y_true=np.array([0, 0, 1, 1]),
        scores=np.array([.1, .8, .9, .2]),
        threshold=.5,
    )
    assert result["confusion_matrix"] == [[1, 1], [1, 1]]
    assert result["precision"] == pytest.approx(.5)
    assert result["recall"] == pytest.approx(.5)
```

- [ ] **Step 2: executar RED**

Run: `.venv/bin/pytest tests/test_anomaly_evaluation.py -q`

Expected: FAIL por módulo ausente.

- [ ] **Step 3: implementar métricas de janela e eventos**

Eventos são sequências contíguas por motor e classe. Um evento é detectado quando existe alerta persistente entre 60 minutos antes do início e o fim; `lead_minutes` é positivo antes do rótulo e negativo quando a detecção atrasa.

- [ ] **Step 4: implementar comparação binária da Sprint 2**

```python
rf_score = 1.0 - classifier.predict_proba(endpoint_features)[:, normal_class_index]
rf_alert = classifier.predict(endpoint_features) > 0
```

As linhas usadas devem ser exatamente os timestamps finais das janelas de teste.

- [ ] **Step 5: executar GREEN e suíte completa**

Run: `.venv/bin/pytest -q`

Expected: todos os testes passam.

- [ ] **Step 6: commit**

```bash
git add src/anomaly_evaluation.py tests/test_anomaly_evaluation.py
git commit -m "feat: evaluate anomaly windows and fault events"
```

---

### Task 4: Contrato do agente e pipeline reproduzível

**Files:**
- Create: `src/anomaly_service.py`
- Create: `src/anomaly_reporting.py`
- Create: `src/run_sprint3.py`
- Create: `tests/test_anomaly_service.py`
- Create: `tests/test_sprint3_smoke.py`

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: `build_agent_payload()`, sete PNGs, `models/modelo_anomalias.joblib`, `models/anomaly_metrics.json`, `results/anomaly_scores.csv`, `results/motor_ranking.csv` e `docs/sprint3_report.md`.

- [ ] **Step 1: escrever teste do payload conversacional**

```python
def test_agent_payload_reports_score_severity_and_dominant_sensor():
    payload = build_agent_payload(
        motor_id=7, timestamp="2026-01-01T12:00:00", score=.40,
        threshold=.20, persistent=True,
        sensor_errors={"vibracao_mm_s": .8, "corrente_a": .3},
    )
    assert payload["severity"] == "high"
    assert payload["dominant_sensors"][0] == "vibracao_mm_s"
    assert "inspeção" in payload["explanation"].lower()
```

- [ ] **Step 2: executar RED e implementar o contrato determinístico**

Run: `.venv/bin/pytest tests/test_anomaly_service.py -q`

Expected antes: FAIL; depois: PASS.

- [ ] **Step 3: escrever smoke test com amostra pequena**

O smoke test executará `run_pipeline(max_motors=6, save_artifacts=False)` e verificará que os três modelos retornam scores finitos, thresholds positivos e métricas com valores entre 0 e 1.

- [ ] **Step 4: executar RED do orquestrador**

Run: `.venv/bin/pytest tests/test_sprint3_smoke.py -q`

Expected: FAIL por `run_pipeline` ausente.

- [ ] **Step 5: implementar pipeline e geradores de artefatos**

`run_pipeline()` deve receber `save_artifacts`, `output_root` e `max_motors`; com persistência habilitada, salvar JSON usando conversão explícita de NumPy/Timestamp para tipos nativos. As figuras devem usar backend `Agg`.

- [ ] **Step 6: executar GREEN e suíte completa**

Run: `.venv/bin/pytest -q`

Expected: todos os testes passam.

- [ ] **Step 7: executar pipeline completo**

Run: `.venv/bin/python src/run_sprint3.py`

Expected: modelos, métricas, CSVs, relatório e sete PNGs são recriados sem entrada manual.

- [ ] **Step 8: commit**

```bash
git add src/anomaly_service.py src/anomaly_reporting.py src/run_sprint3.py tests/test_anomaly_service.py tests/test_sprint3_smoke.py models results figuras docs/sprint3_report.md
git commit -m "feat: generate sprint 3 anomaly deliverables"
```

---

### Task 5: Notebook acadêmico executado e documentação

**Files:**
- Create: `src/build_sprint3_notebook.py`
- Create: `notebooks/sprint3_anomalias.ipynb`
- Create: `requisitos/sprintGenAI_s3.txt`
- Modify: `README.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: artefatos finais da Task 4.
- Produces: notebook com 12 seções do enunciado, instruções de reprodução e checklist final.

- [ ] **Step 1: criar o gerador do notebook**

O notebook deve conter: problema; dados; EDA; baseline; preparação; modelos; avaliação;
casos anômalos; comparação Sprint 2; visualizações; integração conversacional; limitações e reprodução. As células de código devem importar módulos do `src` e exibir métricas/figuras geradas, sem copiar lógica do pipeline.

- [ ] **Step 2: gerar e executar o notebook**

```bash
.venv/bin/python src/build_sprint3_notebook.py
.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks/sprint3_anomalias.ipynb
```

Expected: execução termina com código 0 e o notebook contém outputs.

- [ ] **Step 3: atualizar README e enunciado**

README deve documentar problema, estrutura, comandos exatos, resultados lidos de `anomaly_metrics.json`, comparação com Sprint 2, limitações e checklist 1–12. `.gitignore` deve ignorar caches/testes, preservando modelos e resultados entregáveis.

- [ ] **Step 4: validar notebook estruturalmente**

Run: `.venv/bin/python - <<'PY'`

```python
import nbformat
nb = nbformat.read("notebooks/sprint3_anomalias.ipynb", as_version=4)
assert not [o for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", []) if o.get("output_type") == "error"]
assert sum(c.cell_type == "markdown" for c in nb.cells) >= 12
assert any(c.cell_type == "code" and c.get("outputs") for c in nb.cells)
```

- [ ] **Step 5: commit**

```bash
git add .gitignore README.md requisitos/sprintGenAI_s3.txt src/build_sprint3_notebook.py notebooks/sprint3_anomalias.ipynb
git commit -m "docs: complete sprint 3 academic presentation"
```

---

### Task 6: Auditoria final requisito por requisito

**Files:**
- Modify only if verification identifies a concrete defect.

**Interfaces:**
- Consumes: entrega completa.
- Produces: evidência final de testes, reprodução, notebook e cobertura dos 12 entregáveis.

- [ ] **Step 1: executar testes e pipeline do zero**

```bash
.venv/bin/pytest -q
.venv/bin/python src/run_sprint3.py
```

- [ ] **Step 2: reexecutar notebook**

```bash
.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=1200 notebooks/sprint3_anomalias.ipynb
```

- [ ] **Step 3: auditar artefatos e números**

Conferir JSON/CSVs finitos, sete figuras não vazias, modelo carregável, README sem números divergentes, notebook sem erro e relatório com os 12 itens. Conferir que `.env` não está versionado e que nenhuma credencial aparece no diff.

- [ ] **Step 4: revisar Git e diff**

```bash
git status --short
git diff main...HEAD --check
git log --oneline --decorate main..HEAD
```

- [ ] **Step 5: commit apenas se a auditoria exigir correções**

```bash
git add README.md docs/sprint3_report.md models/anomaly_metrics.json results figuras notebooks/sprint3_anomalias.ipynb
git commit -m "fix: address sprint 3 verification findings"
```

- [ ] **Step 6: declarar pronto somente com todas as evidências verdes**

Relatar branch/worktree, métricas finais, testes, artefatos, limitações e o gate externo restante: revisão do grupo e eventual push/PR, que não serão realizados sem pedido explícito.
