# Sprint 3 Authorial Finalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finalizar as etapas autorais 1 e 2 com conteúdo escrito pelo grupo, consolidá-las no documento vivo e, somente então, produzir o plano definitivo do vídeo.

**Architecture:** O fluxo separa autoria e processamento. O grupo produz as decisões e percepções; o agente pode transcrever, padronizar e validar cobertura sem inventar conteúdo. A integração técnica ocorre no Markdown canônico, seguida de geração DOCX, renderização PDF e auditorias.

**Tech Stack:** Markdown, Python 3.12, python-docx, LibreOffice headless, Poppler, pytest e Streamlit.

**Spec:** `docs/superpowers/specs/2026-08-31-sprint3-governance-decision-design.md`

## Global Constraints

- A matriz de supervisão humana não pode ser escrita por IA.
- As considerações finais não podem ser escritas por IA.
- O agente pode fazer perguntas, transcrever, corrigir ortografia sem mudar sentido, formatar e apontar lacunas.
- Nenhuma ação automática pode autorizar parada física do motor ou da planta.
- O documento final deve manter Lista de Figuras, legenda acima e fonte abaixo.
- O vídeo deve durar entre 3 e 5 minutos e demonstrar a aplicação.
- Não fazer commit, merge ou push sem escolha explícita de Ricardo.

---

### Task 1: Matriz autoral de supervisão humana

**Files:**
- Modify: `docs/gov/matriz_supervisao_PREENCHER_PELO_GRUPO.md`
- Later consume: `docs/gov/sprint3_documento_vivo.md`

**Interfaces:**
- Consumes: respostas literais do grupo para quatro ou mais cenários Forzy.
- Produces: tabela Markdown com sete colunas completas e aprovação explícita do grupo.

- [x] **Step 1: Fazer a coleta autoral**

Para cada cenário, o grupo deve responder com frases próprias:

1. Qual situação concreta da Forzy está sendo analisada?
2. Quais dados, fórmulas, thresholds ou manuais estão disponíveis?
3. Qual contexto só o especialista percebe?
4. O que a IA pode fazer automaticamente?
5. Qual decisão permanece humana?
6. Quem assume o caso?
7. Por que esse limite de autonomia é adequado?

- [x] **Step 2: Exigir cobertura mínima**

A matriz só avança se contiver pelo menos quatro cenários e cobrir, no conjunto:

- leitura normal ou atenção;
- anomalia persistente;
- dado inválido ou inconsistente;
- baixa confiança, ruído externo, manutenção recente ou mudança de carga;
- handoff para um papel humano identificado.

- [x] **Step 3: Transcrever sem criar decisões**

Copiar as respostas do grupo para as sete colunas. É permitido corrigir ortografia e padronizar nomes como `Circuit Breaker`, `Engenheiro de Manutenção` e `handoff`, sem acrescentar justificativas que não tenham sido fornecidas.

- [x] **Step 4: Validar a matriz**

Executar a revisão manual com estes critérios:

- nenhuma célula contém `[PREENCHER]`;
- informação explícita e tácita não são descritas como sinônimos;
- a ação da IA é observacional, registral ou de encaminhamento;
- parada física, descarte de evidência e substituição do especialista aparecem como ações proibidas ou humanas;
- cada handoff tem gatilho, destinatário e evidência mínima;
- Ricardo confirma: `A matriz representa as decisões do grupo.`

Comando auxiliar de validação textual:

```bash
rg -n '\[PREENCHER\]|PREENCHIMENTO AUTORAL' docs/gov/matriz_supervisao_PREENCHER_PELO_GRUPO.md
```

Resultado esperado após aprovação: nenhuma ocorrência em células ou avisos pendentes.

---

### Task 2: Considerações finais autorais

**Files:**
- Modify: `docs/gov/conclusao_PREENCHER_PELO_GRUPO.md`
- Later consume: `docs/gov/sprint3_documento_vivo.md`

**Interfaces:**
- Consumes: percepções literais dos integrantes após testar a aplicação e revisar a matriz.
- Produces: conclusão autoral aprovada pelo grupo, com visão crítica, ética e industrial.

- [x] **Step 1: Fazer o teste autoral antes da escrita**

Cada integrante deve testar ou observar ao menos um dos cinco cenários da aplicação e registrar uma frase própria sobre o que funcionou, o que gerou dúvida ou o que exigiu supervisão.

Comando para abrir a aplicação:

```bash
.venv/bin/streamlit run app.py
```

- [x] **Step 2: Coletar respostas do grupo**

O grupo deve responder, sem texto gerado por IA:

1. O que os Metric Contracts tornaram mais confiável?
2. Em qual caso o Circuit Breaker evitou uma decisão precipitada?
3. Qual limite ético de autonomia foi adotado?
4. O que impede uso industrial imediato?
5. Como a experiência do engenheiro altera a interpretação?
6. Qual foi o ganho mais relevante entre as três sprints?

- [x] **Step 3: Montar o texto autoral**

O grupo deve combinar suas respostas em três a cinco parágrafos, cobrindo evolução, ganho técnico, papel humano, limitação industrial e posição ética. O agente pode corrigir ortografia ou coesão somente após receber o texto integral, preservando as ideias e o vocabulário decisório do grupo.

- [x] **Step 4: Validar a conclusão**

Critérios de aceite:

- não contém `[ESCREVER AQUI]`;
- cita elementos concretos da Forzy, como thresholds, Circuit Breaker ou handoff;
- contém ao menos uma limitação real do protótipo;
- contém uma posição explícita sobre autonomia e responsabilidade;
- não promete implantação industrial nem atribui causalidade a uma anomalia;
- Ricardo confirma: `A conclusão representa a visão crítica do grupo.`

Comando auxiliar:

```bash
rg -n '\[ESCREVER AQUI\]|PREENCHIMENTO AUTORAL' docs/gov/conclusao_PREENCHER_PELO_GRUPO.md
```

Resultado esperado após aprovação: nenhuma ocorrência pendente.

---

### Task 3: Consolidação e validação do documento final

**Files:**
- Modify: `docs/gov/sprint3_documento_vivo.md`
- Modify if pagination changes: `scripts/build_gov_documents.py`
- Regenerate: `docs/gov/challenge_sprint3_gov.docx`
- Test: `tests/test_gov_document_builder.py`

**Interfaces:**
- Consumes: matriz e conclusão aprovadas nas Tasks 1 e 2.
- Produces: documento final sem avisos autorais pendentes, visualmente auditado.

- [x] **Step 1: Criar o teste de ausência de placeholders**

Adicionar ao teste do gerador uma leitura de `word/document.xml` que rejeite os textos `PREENCHIMENTO OBRIGATÓRIO PELO GRUPO`, `SEÇÃO AUTORAL — NÃO PREENCHIDA POR IA`, `[PREENCHER]` e `[ESCREVER AQUI]`.

- [x] **Step 2: Confirmar que o teste falha antes da integração**

```bash
.venv/bin/pytest tests/test_gov_document_builder.py -q
```

Resultado esperado: falha indicando pelo menos um aviso autoral ainda presente.

- [x] **Step 3: Integrar a matriz aprovada**

Substituir o aviso da seção 5.6 pela tabela literal aprovada em `matriz_supervisao_PREENCHER_PELO_GRUPO.md`. Não resumir, completar ou reescrever justificativas.

- [x] **Step 4: Integrar a conclusão aprovada**

Substituir o aviso da seção 7 pelo texto literal aprovado em `conclusao_PREENCHER_PELO_GRUPO.md`. Ajustes permitidos: ortografia, pontuação e concordância que não mudem a posição do grupo.

- [x] **Step 5: Gerar a primeira versão consolidada**

```bash
/tmp/forzy-gov-docx.SbvBav/venv/bin/python scripts/build_gov_documents.py
```

- [x] **Step 6: Renderizar e conferir paginação**

```bash
/tmp/forzy-gov-docx.SbvBav/venv/bin/python \
  /home/ricardo/.codex/plugins/cache/openai-primary-runtime/documents/26.826.12353/skills/documents/render_docx.py \
  docs/gov/challenge_sprint3_gov.docx \
  --output_dir /tmp/forzy-gov-final-render --emit_pdf
```

Comparar as páginas reais das seções 5, 6 e 7 com o sumário estático. Se mudarem, atualizar somente os números correspondentes em `add_toc()` e renderizar novamente.

- [x] **Step 7: Executar auditorias estruturais**

```bash
/tmp/forzy-gov-docx.SbvBav/venv/bin/python \
  /home/ricardo/.codex/plugins/cache/openai-primary-runtime/documents/26.826.12353/skills/documents/scripts/table_geometry.py \
  docs/gov/challenge_sprint3_gov.docx

/tmp/forzy-gov-docx.SbvBav/venv/bin/python \
  /home/ricardo/.codex/plugins/cache/openai-primary-runtime/documents/26.826.12353/skills/documents/scripts/a11y_audit.py \
  docs/gov/challenge_sprint3_gov.docx \
  --out_json /tmp/forzy-gov-final-a11y.json
```

Resultados esperados: geometria `OK` e zero achados de acessibilidade.

- [x] **Step 8: Executar a validação completa**

```bash
.venv/bin/pytest -q
git diff --check
```

Resultados esperados: todos os testes aprovados e nenhuma saída de `git diff --check`.

- [x] **Step 9: Fazer revisão visual de 100% das páginas**

Verificar capa, resumo, Lista de Figuras, sumário, todos os quadros, matriz, cinco evidências, conclusão e paginação. Nenhuma página pode conter corte, skeleton, placeholder ou texto fora das margens.

---

### Task 4: Planejamento definitivo do vídeo com Ricardo

**Files:**
- Modify after Tasks 1–3: `docs/gov/roteiro_video.md`

**Interfaces:**
- Consumes: matriz, conclusão e documento final aprovados.
- Produces: roteiro cronometrado, divisão de falas, ordem dos cliques e checklist de gravação.

- [x] **Step 1: Selecionar quem apresenta cada trecho**

Planejamento preparado para Ricardo como apresentador principal. Se outro integrante participar, os blocos já cronometrados podem ser delegados sem alterar a sequência.

- [x] **Step 2: Converter as decisões autorais em fala**

Usar exclusivamente as ideias aprovadas nas Tasks 1 e 2 para escrever tópicos de fala, sem leitura literal do documento.

- [x] **Step 3: Fixar uma duração-alvo entre 4:00 e 4:30**

Planejar blocos com margem segura dentro do limite de 3–5 minutos e reservar aproximadamente 20 segundos para transições.

- [x] **Step 4: Planejar a sequência da aplicação**

Ordem mínima: Operação normal → Faixa de atenção → Anomalia confirmada → Circuit Breaker por dado inválido → Handoff por baixa confiança.

- [ ] **Step 5: Validar um ensaio cronometrado**

O vídeo só estará pronto para gravação final se o ensaio durar de 3:30 a 4:40, todos os thresholds estiverem legíveis e a defesa autoral não for lida do documento.
