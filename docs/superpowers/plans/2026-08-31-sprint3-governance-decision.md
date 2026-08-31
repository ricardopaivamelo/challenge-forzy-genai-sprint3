# Sprint 3 GOV — Implementation Plan

> Execute em ordem, com TDD para todo comportamento de produção. Não gerar o conteúdo da
> matriz de supervisão nem da conclusão autoral.

**Goal:** Entregar uma camada auditável de governança sobre o detector de anomalias da Forzy,
com Metric Contracts, Circuit Breaker, handoff humano, aplicação e evidências FIAP.

**Architecture:** Contratos configuráveis classificam sensores; um serviço de governança
valida dados, combina thresholds físicos, score e persistência, aplica Circuit Breaker e gera
uma decisão determinística. O Streamlit apenas apresenta e coleta validação humana.

**Stack:** Python 3.12, pandas, NumPy, scikit-learn/joblib, Streamlit, pytest e python-docx.

**Spec:** `docs/superpowers/specs/2026-08-31-sprint3-governance-decision-design.md`

## Task 1 — Contratos e classificação de sensores

**Files:**

- Create: `config/metric_contracts.json`
- Create: `src/governance_contracts.py`
- Create: `tests/test_governance_contracts.py`

1. Escrever testes de fronteira para normal, atenção e crítico.
2. Executar o teste e confirmar falha pela ausência da implementação.
3. Criar dataclasses para contrato e classificação.
4. Carregar e validar contratos de temperatura, vibração e aceleração.
5. Executar teste focal e suíte existente.

## Task 2 — Circuit Breaker e decisão governada

**Files:**

- Create: `src/governance_service.py`
- Create: `tests/test_governance_service.py`

1. Escrever testes para normal, atenção, alerta persistente e handoff.
2. Escrever um teste por causa de bloqueio: missing, inválido, stale, duplicado,
   incompleto, baixa confiança, sem persistência e divergência.
3. Confirmar RED.
4. Implementar validação, breaker e payload auditável mínimos.
5. Confirmar GREEN e refatorar sem mudar comportamento.

## Task 3 — Aceleração simulada

**Files:**

- Create: `src/acceleration.py`
- Create: `tests/test_acceleration.py`
- Create: `results/acceleration_contract_metrics.json`
- Modify: `src/run_sprint3.py`

1. Testar determinismo, não negatividade e correlação positiva com vibração.
2. Confirmar RED.
3. Gerar `aceleracao_g` com seed explícita e método documentado.
4. Calibrar atenção/crítico somente em leituras `falha == 0`.
5. Persistir distribuição e limites auditáveis.

## Task 4 — Integração com o payload existente

**Files:**

- Modify: `src/anomaly_service.py`
- Modify: `tests/test_anomaly_service.py`

1. Testar que o payload preserva o diagnóstico técnico e inclui a decisão de governança.
2. Confirmar RED.
3. Integrar sem permitir que texto de LLM altere score, threshold ou breaker.
4. Executar testes focais e regressão.

## Task 5 — Aplicação Streamlit

**Files:**

- Create: `app.py`
- Create: `src/demo_scenarios.py`
- Create: `tests/test_demo_scenarios.py`
- Create: `tests/test_app_smoke.py`
- Modify: `requirements.txt`

1. Testar os cinco cenários como dados puros antes da UI.
2. Implementar cenários determinísticos.
3. Construir dashboard com controles, limites, breaker, decisão e validação humana.
4. Usar `streamlit.testing.v1.AppTest` para smoke test, se disponível.
5. Validar execução local sem API externa.

## Task 6 — Evidências e documentação viva

**Files:**

- Create: `docs/gov/sprint3_documento_vivo.md`
- Create: `docs/gov/matriz_supervisao_PREENCHER_PELO_GRUPO.md`
- Create: `docs/gov/conclusao_PREENCHER_PELO_GRUPO.md`
- Create: `docs/gov/roteiro_video.md`
- Create: `docs/gov/metric_contracts.docx`
- Create: `docs/gov/challenge_sprint3_gov.docx`
- Create: `figuras/gov_s3_*.png`

1. Reconstruir a estrutura viva usando CS1 e CS2, preservando conteúdo anterior.
2. Inserir os novos capítulos técnicos e limitações específicas da Forzy.
3. Criar matriz e conclusão somente como formulários vazios.
4. Catalogar figuras com legenda e fonte FIAP.
5. Renderizar os DOCX em PNG e revisar todas as páginas.

## Task 7 — Verificação final

1. Executar `.venv/bin/pytest -q`.
2. Executar o pipeline integral e confirmar artefatos reproduzíveis.
3. Executar o smoke test da aplicação.
4. Conferir os cinco cenários e o fail-closed do Circuit Breaker.
5. Revisar cada critério do barema contra evidência concreta.
6. Relatar separadamente o que está pronto e o que depende de autoria/gravação do grupo.
