# Challenge Sprint 3 GOV — Inteligência Operacional e Governança da Decisão

## Contexto

A entrega evolui a documentação viva da Forzy e adiciona governança ao detector de
anomalias concluído na Sprint 3 de GenAI. O novo sistema deve tornar explícitos os limites
físicos dos sensores, a regra de anomalia, as condições que impedem uma decisão automática e
o momento em que a decisão passa para um especialista.

O pipeline existente usa janelas de 30 minutos, threshold calibrado no percentil 99 da
validação e persistência de três janelas. Ele produz score, severidade e sensores dominantes,
mas ainda não possui Metric Contracts, aceleração independente, Circuit Breaker, handoff
formal ou aplicação interativa.

## Decisões de escopo

- Reaproveitar o pipeline de anomalias sem retreinar modelos desnecessariamente.
- Acrescentar `aceleracao_g` como métrica simulada e auditável, derivada de vibração com
  ruído determinístico e limites calibrados somente em leituras normais.
- Separar thresholds físicos dos sensores do threshold estatístico do modelo.
- Usar o Autoencoder como score de ML exibido por padrão; manter os demais detectores para
  comparação e auditoria.
- Construir uma aplicação Streamlit local para a demonstração de 3–5 minutos.
- Restringir automações a classificação, registro, exibição e solicitação de inspeção.
  Nenhuma parada física de motor ou planta será executada automaticamente.
- Não redigir a matriz de supervisão nem a conclusão autoral. O projeto fornecerá somente
  estruturas vazias e perguntas para preenchimento do grupo.

## Fluxo de decisão

1. Receber leituras de temperatura, vibração e aceleração, timestamp e metadados.
2. Validar schema, unidade, completude, atualidade e coerência física.
3. Classificar cada sensor por seu Metric Contract.
4. Comparar o score do modelo com seu threshold e verificar persistência.
5. Avaliar o Circuit Breaker.
6. Produzir uma decisão governada: `normal`, `attention`, `alert`, `blocked` ou `handoff`.
7. Exibir a explicação, registrar evidências e permitir validação humana.

## Metric Contracts

Cada contrato terá identificador, descrição, unidade, fonte, frequência, owner, versão,
limites de atenção/crítico, política de persistência e ação permitida. Os valores iniciais de
temperatura e vibração serão tratados como hipóteses internas já usadas pelo grupo e serão
comparados com a base antes da documentação final:

- temperatura: atenção a partir de 90 °C; crítico a partir de 100 °C;
- vibração: atenção a partir de 6 mm/s; crítico a partir de 9 mm/s;
- aceleração: limites calculados sobre a distribuição normal simulada e registrados junto
  com o método de calibração.

## Circuit Breaker

O Circuit Breaker funcionará em modo seguro: um problema de dados bloqueia o alerta decisório,
mas preserva o evento e informa o motivo. Condições mínimas:

- campo ausente, nulo, não numérico ou fisicamente inválido;
- timestamp duplicado ou leitura com mais de cinco minutos;
- menos de 90% de completude na janela de 30 minutos;
- unidade ou versão do contrato incompatível;
- artefato de modelo indisponível;
- score acima do threshold sem três janelas persistentes;
- confiança do classificador abaixo de 85%;
- divergência material entre modelo e thresholds físicos.

## Handoff humano

O payload de handoff conterá motor, timestamp, leituras, estados dos sensores, score,
threshold, persistência, confiança, motivo, evidências e papel destinatário. A aplicação
permitirá registrar `pending`, `validated` ou `rejected`, com justificativa humana.

O conteúdo da matriz que separa informação explícita e tácita será preenchido pelo grupo.

## Aplicação e evidências

O dashboard Streamlit terá seleção de cenário/motor, controles de leituras, cartões de estado,
gráficos com limites, status do Circuit Breaker, decisão automática e formulário de validação
humana. Cinco cenários reproduzíveis suportarão documento e vídeo: normal, atenção, anomalia
persistente, dados inválidos e handoff.

As capturas serão salvas com nomes estáveis, legenda acima e fonte abaixo no documento.

## Verificação

- testes de fronteira para todos os thresholds;
- testes de cada condição do Circuit Breaker;
- testes das transições de decisão e do payload de handoff;
- teste determinístico da aceleração simulada;
- smoke test da aplicação;
- suíte completa `pytest -q`;
- execução manual dos cinco cenários;
- renderização do DOCX em PNG e inspeção de todas as páginas.

## Limitações declaradas

Os dados e a aceleração são sintéticos; thresholds não representam validação industrial; o
erro por sensor não comprova causa física; a decisão de manutenção permanece humana.
