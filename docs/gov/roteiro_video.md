# Planejamento da Etapa 4 — Vídeo de Defesa

## Objetivo e formato

- **Apresentador principal:** Ricardo.
- **Duração-alvo:** 4 minutos e 20 segundos.
- **Faixa válida:** entre 3 e 5 minutos.
- **Formato:** gravação da aplicação funcionando, com explicação oral e sem leitura do documento.
- **Tela principal:** aplicação Streamlit aberta com a barra lateral e os valores legíveis.

Se outro integrante participar, a divisão sugerida é: Ricardo apresenta contexto, Circuit Breaker,
handoff e defesa autoral; o outro integrante apresenta Metric Contracts e anomalia confirmada.

## Preparação antes de gravar

1. Abrir um terminal na pasta do projeto.
2. Executar `./.venv/bin/streamlit run app.py`.
3. Abrir o endereço informado pelo Streamlit no navegador.
4. Deixar a barra lateral aberta e ajustar o zoom para que thresholds, score, confiança e decisão
   apareçam sem rolagem horizontal.
5. Fechar notificações e outras janelas que possam aparecer durante a gravação.
6. Fazer um teste curto de microfone e confirmar que a aplicação responde à troca de cenário.

## Sequência cronometrada

### 0:00–0:20 — Contexto e objetivo

**Na tela:** aplicação aberta em **Operação normal**.

**Tópicos de fala:**

- identificar a solução Forzy e o monitoramento do motor;
- explicar que a Sprint 3 colocou regras de governança sobre os alertas;
- antecipar que a aplicação distingue alerta, decisão automática permitida e decisão humana.

**Transição:** apontar a seleção de cenários na barra lateral.

### 0:20–0:55 — Metric Contracts e operação normal

**Clique:** manter **Operação normal**.

**Mostrar:**

- temperatura, vibração e aceleração com suas unidades;
- valor lido, faixa atual e limite contratado;
- ausência de bloqueio e ação apenas de monitoramento.

**Tópicos de fala:** os contratos formalizam o significado de cada métrica, seus limites e as ações
permitidas. Os valores foram definidos para o protótipo e precisam de validação industrial.

### 0:55–1:20 — Faixa de atenção

**Clique:** selecionar **Faixa de atenção**.

**Mostrar:** valor que ultrapassou a faixa normal e threshold correspondente.

**Tópicos de fala:** entrar em atenção não confirma falha. O sistema destaca e monitora a condição,
sem mandar parar o equipamento.

### 1:20–2:00 — Anomalia confirmada

**Clique:** selecionar **Anomalia confirmada**.

**Mostrar:**

- score `1,3000`, acima do threshold do Autoencoder `0,9513`;
- persistência por três janelas;
- evidência física crítica;
- ação de registrar o alerta e solicitar inspeção humana.

**Tópicos de fala:** uma leitura isolada não basta. O alerta só é confirmado quando há score acima do
limite, persistência e evidência física válida. Mesmo confirmado, o sistema não executa parada física.

### 2:00–2:45 — Circuit Breaker por dado inválido

**Clique:** selecionar **Circuit Breaker por dado inválido**.

**Mostrar:** `sensor_error`, decisão `BLOCKED`, motivo do bloqueio e leituras preservadas.

**Tópicos de fala:** nos testes, a temperatura chegou inválida enquanto a vibração estava crítica. O
sistema preferiu bloquear a decisão, pois dados incompletos poderiam criar um falso alerta e uma
decisão incorreta. O evento continua registrado para análise.

### 2:45–3:30 — Handoff por baixa confiança

**Clique:** selecionar **Handoff por baixa confiança**.

**Mostrar:** confiança de `72%`, limite mínimo de `85%`, Circuit Breaker e área de decisão humana.

**Tópicos de fala:** o engenheiro deve avaliar o contexto que a aplicação não conhece, como uma
manutenção recente, outra máquina ou uma obra causando vibração. Ele recebe as evidências e registra
se valida ou rejeita o alerta.

### 3:30–4:05 — Defesa autoral do grupo

**Na tela:** manter o handoff ou retornar brevemente ao alerta confirmado.

**Usar estas ideias como guia, sem ler literalmente:**

- agora o alerta mostra qual valor ultrapassou qual limite, dando uma base concreta para confiar ou
  desconfiar;
- a parada do motor nunca deve partir apenas da máquina, porque afeta segurança e produção;
- os dados são simulados e a aceleração é calculada a partir da vibração, então os limites precisam
  ser recalibrados antes do uso em uma fábrica;
- a governança evoluiu de regras escritas para regras visíveis e executáveis, capazes de travar o
  próprio sistema quando falta base para decidir.

### 4:05–4:20 — Encerramento

**Tópicos de fala:** resumir que Metric Contracts, Circuit Breaker e handoff aumentam a confiabilidade
sem substituir o especialista; encerrar identificando a entrega como Challenge Sprint 3 da Forzy.

## Ordem exata dos cliques

1. **Operação normal**.
2. **Faixa de atenção**.
3. **Anomalia confirmada**.
4. **Circuit Breaker por dado inválido**.
5. **Handoff por baixa confiança**.
6. No handoff, mostrar rapidamente as opções de decisão, sem registrar uma decisão improvisada.

## Critérios para aprovar o ensaio

- duração entre **3:30 e 4:40**, criando margem para a gravação final permanecer entre 3 e 5 minutos;
- os cinco cenários aparecem na ordem planejada;
- valores, thresholds, score, confiança e status `BLOCKED` ficam legíveis;
- há demonstração prática, não leitura do documento;
- a explicação sobre supervisão humana corresponde às decisões aprovadas pelo grupo;
- a defesa autoral é dita com naturalidade e preserva a visão crítica confirmada pelo grupo;
- nenhuma afirmação sugere que a aplicação pode parar fisicamente o motor;
- o vídeo final começa e termina sem trechos de configuração, espera ou erro de navegação.

## Plano de contingência

- Se a gravação passar de 5 minutos, reduzir a explicação da operação normal e das transições; não
  remover Circuit Breaker, handoff nem defesa autoral.
- Se ficar abaixo de 3 minutos, explicar melhor a diferença entre alerta confirmado e parada física.
- Se a aplicação falhar durante a gravação, interromper e recomeçar; não substituir a demonstração
  por leitura do DOCX ou por imagens estáticas.
