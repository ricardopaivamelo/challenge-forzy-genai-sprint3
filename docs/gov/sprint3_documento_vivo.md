# GOVERNANÇA EM IA E BUSINESS ANALYTICS

## Inteligência Operacional e Governança da Decisão — Challenge Sprint 3

**Solução Digital Twin Forzy**<br>
**Ano:** 2026<br>
**Professor:** Marco Fontoura

**Integrantes**

- RM566479 — Jonas Alaf da Silva
- RM562358 — Murilo Benhossi
- RM565460 — Pedro Leal Murad
- RM561401 — Luís Fernando de Oliveira Salgado
- RM565522 — Ricardo de Paiva Melo
- RM553273 — Nicolas Lemos Ribeiro

## RESUMO

Este documento vivo consolida a evolução da governança da plataforma Forzy. A primeira
sprint estruturou acesso, explicabilidade, rastreabilidade e fairness. A segunda levou esses
controles para a interface e para a navegação dos ativos. A terceira formaliza os limites da
inteligência operacional por meio de Metric Contracts, thresholds físicos, regra de anomalia,
Circuit Breaker e protocolo de handoff humano. A aplicação demonstrável mantém a decisão
física sob responsabilidade de um especialista e registra por que cada alerta foi emitido,
bloqueado ou encaminhado.

**Palavras-chave:** Governança de IA. Metric Contract. Threshold. Circuit Breaker. Handoff.
Manutenção preditiva.

## LISTA DE FIGURAS

- Figura 1 — Operação dos sensores dentro dos Metric Contracts ................................ 13
- Figura 2 — Sensor na faixa de atenção ........................................................ 14
- Figura 3 — Anomalia persistente confirmada para inspeção humana ............................... 15
- Figura 4 — Circuit Breaker acionado por dado inválido ......................................... 16
- Figura 5 — Handoff acionado por baixa confiança ................................................ 17

# 1 INTRODUÇÃO

A plataforma Forzy monitora motores elétricos industriais por meio de dados de rotação,
vibração, temperatura e corrente. O trabalho de GenAI acrescentou classificação de falhas e
detecção semissupervisionada de anomalias em janelas temporais. A existência de um modelo,
entretanto, não define sozinha quando uma recomendação é confiável ou qual ação pode ser
executada sem supervisão.

Nesta sprint, a governança é tratada como uma camada operacional sobre o modelo. Seu papel é
formalizar os limites dos sensores, separar desvio físico de desvio estatístico, bloquear
alertas em condições de dados ou incerteza inadequadas e transferir decisões críticas para o
especialista. Essa evolução responde diretamente aos feedbacks anteriores: restaura a lógica
de documento vivo, recupera o detalhamento da primeira sprint e substitui o mockup estático
por uma aplicação executável.

# 2 CONTEXTUALIZAÇÃO DA SOLUÇÃO FORZY

A solução é organizada em cinco módulos integrados: extração de dados, registro de
equipamentos, interface, modelagem e integração conversacional. O banco acadêmico contém
30.000 leituras sintéticas de 20 motores, registradas em intervalos de um minuto durante 25
horas. As variáveis originais são rotação, vibração, temperatura e corrente.

O detector de anomalias aprende o comportamento normal de cada motor por mediana e intervalo
interquartil das primeiras 30 leituras. Em seguida, processa janelas de 30 minutos com avanço
de cinco minutos. O threshold do Autoencoder foi calculado no percentil 99 das janelas normais
de validação e vale 0,9513. Um alerta só é persistente depois de três janelas consecutivas
acima desse valor.

Para atender ao escopo de governança, o protótipo acrescenta `aceleracao_g`. Essa variável é
uma simulação equivalente derivada da vibração RMS, considerando componente dominante de 60
Hz e ruído determinístico. Ela não é apresentada como medição industrial nem passa a integrar
retroativamente as features do modelo treinado.

# 3 EVOLUÇÃO DA GOVERNANÇA — SPRINT 1

## 3.1 Hierarquia e controle de acesso

A primeira sprint definiu quatro papéis operacionais segundo o princípio de menor privilégio.
Essa separação foi preservada porque a nova camada de decisão não pode dar a todos os usuários
o mesmo acesso aos dados, aos parâmetros dos modelos ou aos controles da planta.

O **Técnico de Operação** acompanha valores em tempo real por TAG, recebe alertas em linguagem
operacional, consulta orientações e registra ocorrências. Ele não altera contratos, parâmetros do
modelo ou configurações de segurança. O **Gestor de Planta** acompanha o histórico completo,
relatórios e indicadores operacionais, além de propor alterações de limites que ainda dependem
do processo formal de revisão.

O **Engenheiro de Dados/IA** acessa dados brutos, versões de modelos, métricas e pipelines para
investigar desvios e manter os artefatos. O **Auditor de Segurança/TI** consulta trilhas de
auditoria em modo leitura e verifica quem executou cada ação. Na Sprint 3, o Engenheiro de
Manutenção passa a ser o destinatário operacional do handoff, sem receber permissão para
reescrever retroativamente os registros.

**Quadro 1 — Papéis e responsabilidades na plataforma Forzy**

| Papel | Responsabilidade principal | Relação com a Sprint 3 |
|---|---|---|
| Técnico de Operação | Monitorar motores, receber alertas e registrar ocorrências | Visualiza alertas e evidências, sem alterar contratos |
| Gestor de Planta | Gerenciar ativos, histórico e limites operacionais | Propõe e aprova revisões dos limites da planta |
| Engenheiro de Dados/IA | Validar dados, modelos e pipelines | Mantém versão do modelo e investiga divergências |
| Auditor de Segurança/TI | Consultar logs imutáveis em modo leitura | Audita contrato, breaker, handoff e decisão humana |

Fonte: Elaborado pelos autores (2026), com base na Sprint 1.

**Quadro 2 — Matriz RBAC preservada e refinada**

| Módulo ou recurso | Técnico de Operação | Gestor de Planta | Engenheiro de Dados/IA | Auditor de Segurança/TI |
|---|---|---|---|---|
| Dashboard em tempo real | Leitura | Leitura | Leitura técnica | Auditoria |
| Dados brutos | Negado | Negado | Leitura | Auditoria |
| Alertas de anomalia | Receber e registrar | Receber e acompanhar | Configurar modelo | Auditar |
| Histórico | Últimos 7 dias | Completo | Completo | Completo em leitura |
| Cadastro por visão computacional | Executar captura | Aprovar | Validar algoritmo | Auditar |
| Limites operacionais | Visualizar | Propor e aprovar revisão | Configurar após aprovação | Auditar versão |
| Modelos de ML | Negado | Negado | Acesso completo | Auditar versão |
| Logs de auditoria | Negado | Negado | Consulta técnica limitada | Acesso completo em leitura |
| Chatbot e manuais | Consultar | Consultar | Consultar | Sem acesso operacional |
| Decisão física sobre o motor | Seguir procedimento autorizado | Coordenar procedimento | Sem comando físico | Sem comando físico |

Fonte: Elaborado pelos autores (2026), com base na matriz RBAC da Sprint 1 e nos limites da
Sprint 3.

## 3.2 Cadeia D-I-C-I

O fluxo Dado–Informação–Conhecimento–Inteligência permanece como estrutura explicativa do
ativo. No nível de **Dado**, cada leitura bruta é vinculada ao motor, ao tipo de sensor, ao
timestamp e à unidade recebida. No nível de **Informação**, o pipeline converte o valor para a
unidade contratada e verifica domínio físico, atualidade, completude e duplicidade, produzindo
um estado de qualidade.

No nível de **Conhecimento**, as leituras aprovadas são comparadas com o baseline individual do
motor, com os thresholds físicos e com o histórico de janelas. O modelo calcula o score de
anomalia, mas esse score é tratado como evidência estatística e não como causa física
comprovada. No nível de **Inteligência**, a recomendação passa pelos limites de persistência,
confiança, coerência física e Circuit Breaker antes de chegar ao usuário.

**Quadro 3 — Cadeia D-I-C-I atualizada**

| Nível | Entrada e tratamento | Responsável | Saída governada |
|---|---|---|---|
| Dado | Leitura bruta, motor, timestamp e unidade original | Módulo de extração | Registro identificável da leitura |
| Informação | Conversão de unidade e controles de qualidade | Pipeline de dados | Valor normalizado com estado de qualidade |
| Conhecimento | Baseline, thresholds, histórico e score do modelo | Regras e modelo de ML | Desvio físico ou estatístico contextualizado |
| Inteligência | Persistência, confiança, Circuit Breaker e limites de autonomia | Serviço de governança | Decisão explicável, bloqueio ou handoff |

Fonte: Elaborado pelos autores (2026), a partir da cadeia D-I-C-I da Sprint 1.

Na Sprint 3, a passagem de Conhecimento para Inteligência deixa de ser automática em qualquer
condição. O Circuit Breaker verifica se a recomendação possui qualidade e certeza suficientes.

## 3.3 Explainability

Na primeira sprint, o risco de caixa-preta foi tratado exigindo que todo alerta apresentasse o
sensor envolvido, o valor observado, a referência utilizada, uma explicação compreensível e a
ação recomendada. O nível de detalhe varia conforme o perfil: o Técnico de Operação precisa
entender condição, urgência e ação segura; o Engenheiro de Dados/IA também precisa consultar
score, parâmetros, versão e evidências técnicas.

Na Sprint 3, o alerta executável informa motor, horário, leituras, unidades, threshold
ultrapassado, score do modelo, persistência, confiança, ação permitida e versão do contrato. A
explicação descreve associação e prioridade de inspeção, sem afirmar uma causa física que não
foi confirmada. Essa correção também substitui a proposta inicial de modelos hipotéticos pela
implementação realmente utilizada: baseline estatístico, Isolation Forest e Autoencoder, com o
Autoencoder adotado no cenário demonstrável.

## 3.4 Protocolo de rastreabilidade

O cadastro por Visão Computacional definido na Sprint 1 continua seguindo um fluxo auditável:

1. o técnico autenticado captura a imagem da placa do motor;
2. o algoritmo de visão computacional processa a imagem e registra sua versão;
3. cada campo extraído recebe um score de confiança;
4. campos com confiança inferior a 80% são encaminhados para revisão;
5. o Gestor ou especialista valida os campos sinalizados;
6. o ativo é publicado com seus metadados preservados;
7. o evento é incluído em log append-only com hash de integridade.

Esse protocolo permite reconstruir quem capturou a imagem, qual modelo processou o ativo, quais
campos apresentaram incerteza e quem realizou a validação humana. A Sprint 3 estende o mesmo
princípio aos alertas com os campos `metric_contract_version`, `model_threshold`,
`circuit_breaker_state`, `breaker_reasons`, `handoff_status` e
`human_justification`.

## 3.5 Dicionário de metadados

**Quadro 4 — Metadados obrigatórios preservados da Sprint 1**

| Campo | Tipo | Obrigatoriedade | Finalidade |
|---|---|---|---|
| `asset_tag` | Texto | Sim | Identificar o motor na planta |
| `asset_uuid` | UUID | Sim | Manter identificador interno imutável |
| `registration_timestamp` | ISO 8601 | Sim | Registrar data e hora do cadastro |
| `photo_file_hash` | SHA-256 | Sim | Verificar integridade da imagem |
| `cv_algorithm_id` | Texto | Sim | Identificar o algoritmo de extração |
| `cv_model_version` | Semver | Sim | Registrar a versão do modelo |
| `extraction_confidence` | Número de 0 a 1 | Sim | Medir confiança média da extração |
| `fields_low_confidence` | Lista JSON | Sim | Enumerar campos abaixo do limite |
| `captured_by_user_id` | UUID | Sim | Identificar quem realizou a captura |
| `device_id` | Texto | Sim | Identificar o dispositivo de origem |
| `validated_by_user_id` | UUID | Condicional | Identificar o revisor humano |
| `validation_timestamp` | ISO 8601 | Condicional | Registrar o momento da revisão |
| `data_source` | Enum | Sim | Distinguir visão computacional, entrada manual ou importação |
| `log_entry_hash` | SHA-256 | Sim | Detectar alteração retroativa do log |

Fonte: Elaborado pelos autores (2026), com base no dicionário de rastreabilidade da Sprint 1.

## 3.6 Fairness e limitações

A Sprint 1 identificou seis riscos de representatividade. O **Viés de Marca** ocorre quando uma
marca domina a base; o **Viés de Condição** aparece quando predominam regimes normais; o
**Viés de Idade ou Legado** pode fazer um motor antigo parecer anômalo apenas por seu desgaste
esperado; o **Viés de Faixa de Potência** reduz a generalização fora das potências observadas; o
**Viés Temporal** ignora turnos e sazonalidade; e o **Viés de Confirmação no Labeling** transfere
para o modelo a interpretação de uma única equipe.

**Quadro 5 — Estratégia de curadoria e fairness**

| Frente | Controle preservado | Critério de revisão |
|---|---|---|
| Diversidade de dados | Representar marcas, potências, idades e condições distintas | Medir cobertura antes de treinar |
| Validação multiplanta | Testar em plantas não usadas no treinamento | Comparar queda de desempenho entre contextos |
| Monitoramento por segmento | Calcular precision, recall e F1 por grupo de motor | Investigar disparidades relevantes |
| Feedback operacional | Registrar alertas validados e rejeitados | Revisar dados e thresholds periodicamente |
| Model Card | Documentar dados, versão, limites e condições de uso | Manter 100% dos modelos publicados com ficha atualizada |

Fonte: Elaborado pelos autores (2026), com base na estratégia da Sprint 1.

As metas quantitativas propostas na primeira sprint devem ser tratadas como objetivos de
validação, e não como resultados já comprovados. Na Sprint 3, o risco de um threshold global
favorecer motores próximos ao padrão dominante é reduzido pelo baseline individual por motor e
pelo versionamento dos contratos. Os resultados acadêmicos não autorizam implantação direta em
uma planta real.

# 4 EVOLUÇÃO DA GOVERNANÇA — SPRINT 2

## 4.1 Governança visual

A segunda sprint introduziu os estados “Validado por humano”, “Gerado por IA” e “Pendente de
validação”, além de disclaimers para dado em tempo real, sensor em calibração e alerta de IA.
Esses elementos são preservados e passam a ser alimentados por um fluxo executável.

## 4.2 Rastreabilidade de TAG e localização

Movimentações de ativos continuam exigindo TAG, usuário, timestamp, versão do mapa e método de
validação. A decisão de governança não substitui a identidade do ativo: nenhum alerta pode ser
emitido se a leitura não estiver associada de forma inequívoca a um motor.

## 4.3 Correções aplicadas a partir do feedback

- reincorporação dos papéis, matriz RBAC, cadeia D-I-C-I, protocolo de cadastro, dicionário de metadados e estratégia de fairness da Sprint 1;
- correção do ano de 2025 para 2026;
- preservação da continuidade entre sprints;
- aplicação funcional em substituição ao mockup apenas estático;
- demonstração de thresholds, breaker e handoff diretamente na interface;
- integração da matriz e das considerações finais aprovadas pelo grupo.

# 5 INTELIGÊNCIA OPERACIONAL E GOVERNANÇA DA DECISÃO — SPRINT 3

## 5.1 Metric Contracts

Os contratos formalizam o significado, a unidade, a frequência, o responsável e os limites de
cada métrica. Os valores são válidos apenas para o protótipo acadêmico e devem ser recalibrados
antes de uso industrial.

**Quadro 6 — Síntese dos thresholds dos sensores**

| Métrica | Unidade | Normal | Atenção | Crítico |
|---|---:|---:|---:|---:|
| Temperatura | °C | `< 90` | `90 a < 100` | `≥ 100` |
| Vibração RMS | mm/s | `< 6` | `6 a < 9` | `≥ 9` |
| Aceleração simulada | g | `< 0,1487` | `0,1487 a < 0,1813` | `≥ 0,1813` |

Fonte: Elaborado pelos autores (2026).

Temperatura e vibração utilizam faixas empíricas do protótipo. Os limites da aceleração
correspondem aos quantis 95% e 99% das 26.291 leituras normais simuladas.

Os três contratos completos estão no documento específico de Metric Contracts. Todos usam
frequência de uma leitura por minuto, persistência de três janelas e owner “Engenharia de
Manutenção”. A ação automática máxima é registrar o evento e solicitar inspeção.

## 5.2 Definição operacional de anomalia

O sistema separa três conceitos:

- **desvio físico:** um sensor ultrapassou o limite de atenção ou crítico de seu contrato;
- **desvio estatístico:** o score do Autoencoder ultrapassou 0,9513;
- **anomalia confirmada:** score acima do threshold durante três janelas consecutivas, com
  evidência física e dados aprovados pelo Circuit Breaker.

Uma anomalia representa comportamento fora do padrão aprendido. Ela não comprova a causa da
falha. A classificação supervisionada pode sugerir uma categoria conhecida, mas a validação
física permanece humana.

## 5.3 Ações automáticas permitidas

**Quadro 7 — Autonomia do sistema**

| Estado | Ação automática permitida | Ação proibida |
|---|---|---|
| Normal | Registrar e manter monitoramento | Alterar configuração da planta |
| Atenção | Destacar desvio e acompanhar tendência | Parar motor |
| Anomalia pontual | Aguardar persistência | Emitir alerta crítico definitivo |
| Anomalia confirmada | Registrar alerta e solicitar inspeção | Executar parada física |
| Circuit Breaker | Bloquear decisão e registrar motivo | Ocultar ou descartar o evento |
| Handoff | Encaminhar evidências ao especialista | Substituir a decisão humana |

Fonte: Elaborado pelos autores (2026).

## 5.4 Circuit Breaker

O Circuit Breaker abre e trava o alerta decisório quando a qualidade do dado ou a incerteza não
sustenta uma recomendação autônoma. O evento continua visível para investigação.

Condições implementadas:

- sensor obrigatório ausente, nulo, não numérico ou fora do domínio físico;
- unidade incompatível;
- timestamp duplicado ou leitura atrasada por mais de cinco minutos;
- completude inferior a 90% da janela;
- modelo indisponível;
- score acima do threshold sem persistência;
- confiança da classificação inferior a 85%;
- divergência entre score anômalo e sensores normais, ou sensor crítico e score normal.

## 5.5 Protocolo de handoff humano

Quando o alerta exige conhecimento contextual, o sistema cria um handoff com estado
`pending`. O pacote inclui identificação do motor, leituras, thresholds, score, persistência,
confiança, motivo do breaker, evidências e destinatário. O Engenheiro de Manutenção pode
marcar a recomendação como validada ou rejeitada, registrando justificativa. A alteração
fica vinculada ao alerta e não modifica os fatos produzidos pelo modelo.

## 5.6 Informação explícita e informação tácita

As regras numéricas, unidades, timestamps, versão do modelo e condições de qualidade são
informações explícitas e executáveis. Contexto de planta, ruídos externos, intervenção recente,
mudança de carga e histórico percebido pelo especialista são informações tácitas.

**Quadro 8 — Matriz de supervisão humana**

| Cenário real da Forzy | Informação explícita disponível | Informação tácita percebida pelo especialista | Ação permitida à IA | Decisão reservada ao humano | Papel responsável | Justificativa autoral |
|---|---|---|---|---|---|---|
| Leituras críticas logo após uma manutenção recente. | Temperatura, vibração e aceleração medidas, limites do Metric Contract e histórico do alerta. | O engenheiro conhece a intervenção realizada, as peças alteradas e as condições de partida do equipamento. | Preservar as evidências, registrar o bloqueio de governança e realizar o handoff. | Avaliar se as leituras representam uma falha ou um efeito temporário da manutenção. | Engenheiro de Manutenção. | Uma manutenção recente exige avaliação humana porque a intervenção pode alterar temporariamente as leituras e somente o engenheiro conhece o que foi modificado. |
| Sensor de temperatura inválido enquanto vibração e aceleração estão em faixa crítica. | Status `sensor_error`, leituras disponíveis dos outros sensores, limites contratuais e regras de qualidade dos dados. | O especialista avalia as condições reais do sensor e do equipamento que não aparecem nos dados válidos restantes. | Acionar o Circuit Breaker, preservar todas as leituras e encaminhar o caso. | Confirmar se existe uma anomalia física e decidir a inspeção necessária. | Engenheiro de Manutenção. | Um sensor inválido deve bloquear a decisão porque dados incompletos podem gerar um falso alerta e levar a uma decisão incorreta. |
| Temperatura, vibração e aceleração críticas, score do Autoencoder acima do limite por três janelas e alta confiança. | Leituras válidas, thresholds, score de anomalia, persistência de três janelas e confiança do modelo. | O especialista considera o estado operacional, os riscos da planta e as consequências de uma parada. | Confirmar e priorizar o alerta, registrar as evidências e solicitar inspeção. | Autorizar uma parada física conforme o procedimento de segurança da planta. | Engenheiro de Manutenção ou responsável pelo processo de segurança. | Mesmo com a anomalia confirmada, o sistema não deve parar o motor sozinho porque o alerta auxilia a decisão, mas uma parada física afeta a segurança e a produção e precisa seguir o procedimento da planta. |
| Leituras críticas com 72% de confiança enquanto obras ou outras máquinas produzem vibração externa. | Leituras dos sensores, score, confiança de 72% e limite mínimo de 85% definido no contrato. | O engenheiro percebe a origem externa da vibração e o contexto operacional ao redor do equipamento. | Acionar o Circuit Breaker por baixa confiança, marcar a decisão como pendente e realizar o handoff com as evidências. | Validar ou rejeitar o alerta com justificativa e decidir se alguma intervenção é necessária. | Engenheiro de Manutenção. | Ruídos externos e baixa confiança exigem a análise do engenheiro porque outras máquinas ou obras podem afetar a vibração e uma confiança de 72% ainda deixa dúvida suficiente para exigir avaliação humana. |

Fonte: Elaborado pelos autores (2026).

# 6 EVIDÊNCIAS DE FUNCIONAMENTO

**Figura 1 — Operação dos sensores dentro dos Metric Contracts**

![Operação normal](../../figuras/gov_s3_01_normal.png)

Fonte: Elaborado pelos autores a partir da aplicação Forzy (2026).

**Figura 2 — Sensor na faixa de atenção**

![Faixa de atenção](../../figuras/gov_s3_02_attention.png)

Fonte: Elaborado pelos autores a partir da aplicação Forzy (2026).

**Figura 3 — Anomalia persistente confirmada para inspeção humana**

![Anomalia confirmada](../../figuras/gov_s3_03_alert.png)

Fonte: Elaborado pelos autores a partir da aplicação Forzy (2026).

**Figura 4 — Circuit Breaker acionado por dado inválido**

![Circuit Breaker](../../figuras/gov_s3_04_circuit_breaker.png)

Fonte: Elaborado pelos autores a partir da aplicação Forzy (2026).

**Figura 5 — Handoff acionado por baixa confiança**

![Handoff](../../figuras/gov_s3_05_handoff.png)

Fonte: Elaborado pelos autores a partir da aplicação Forzy (2026).

# 7 CONSIDERAÇÕES FINAIS

Com a definição dos thresholds, quando aparece um alerta, conseguimos abri-lo e verificar qual
valor ultrapassou o limite e qual era o limite esperado. Assim, é possível confiar ou desconfiar
do alerta com base em algo concreto. Nos testes, houve um caso em que o sensor de temperatura
apresentou erro enquanto a vibração estava crítica, e o sistema preferiu segurar o alerta em vez
de confirmar uma falha com dados incompletos.

O grupo considera que a decisão de parar o motor nunca deve ser tomada somente pela máquina,
pois ela afeta a segurança e toda a produção da planta. O alerta deve apoiar a avaliação, mas a
responsabilidade pela parada continua sendo humana.

O protótipo ainda não pode ser usado diretamente em uma fábrica porque todos os dados são
simulados. A aceleração também não vem de um sensor real, pois é calculada com base na vibração.
Por isso, os limites precisariam ser recalibrados antes de qualquer uso industrial. A experiência
do engenheiro continua necessária porque o sistema não consegue saber, por exemplo, que o motor
recebeu manutenção no dia anterior ou que existe uma obra próxima causando vibrações. Esse
contexto muda completamente a forma como a leitura deve ser interpretada.

No começo, a governança era apenas um conjunto de regras escritas. Depois, essas regras passaram
a aparecer na tela e, agora, são executadas de verdade, fazendo com que o próprio sistema
interrompa sua decisão quando não existe base suficiente para decidir.
