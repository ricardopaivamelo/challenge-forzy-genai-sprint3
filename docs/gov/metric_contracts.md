# Metric Contract — Forzy

## 1 Informações gerais

| Campo | Definição |
|---|---|
| Produto | Plataforma Forzy Digital Twin |
| Objetivo | Governar os limites usados nos alertas de motores elétricos |
| Owner | Engenharia de Manutenção |
| Responsável técnico | Engenheiro de Dados/IA |
| Versão | 1.0 |
| Status | Protótipo acadêmico; pendente de validação industrial |
| Frequência | Uma leitura por minuto |
| Revisão | Sempre que houver nova calibração, sensor, planta ou versão do modelo |

## 2 Contrato de temperatura

| Cláusula | Valor |
|---|---|
| Identificador | `temperature` |
| Campo | `temperatura_c` |
| Unidade | °C |
| Domínio físico aceito | 0 a 200 °C |
| Normal | menor que 90 °C |
| Atenção | maior ou igual a 90 °C e menor que 100 °C |
| Crítico | maior ou igual a 100 °C |
| Persistência | Três janelas consecutivas para alerta do modelo |
| Ação automática | Registrar, destacar e solicitar inspeção |
| Ação proibida | Parar o motor ou a planta automaticamente |
| Fonte do limite | Faixas empíricas usadas no protótipo; requer validação industrial |

## 3 Contrato de vibração

| Cláusula | Valor |
|---|---|
| Identificador | `vibration` |
| Campo | `vibracao_mm_s` |
| Unidade | mm/s RMS |
| Domínio físico aceito | 0 a 50 mm/s |
| Normal | menor que 6 mm/s |
| Atenção | maior ou igual a 6 mm/s e menor que 9 mm/s |
| Crítico | maior ou igual a 9 mm/s |
| Persistência | Três janelas consecutivas para alerta do modelo |
| Ação automática | Registrar, destacar e solicitar inspeção |
| Ação proibida | Parar o motor ou a planta automaticamente |
| Fonte do limite | Faixas empíricas usadas no protótipo; requer validação industrial |

## 4 Contrato de aceleração

| Cláusula | Valor |
|---|---|
| Identificador | `acceleration` |
| Campo | `aceleracao_g` |
| Unidade | g |
| Domínio físico aceito | 0 a 5 g |
| Normal | menor que 0,1487 g |
| Atenção | maior ou igual a 0,1487 g e menor que 0,1813 g |
| Crítico | maior ou igual a 0,1813 g |
| Persistência | Três janelas consecutivas para alerta do modelo |
| Ação automática | Registrar, destacar e solicitar inspeção |
| Ação proibida | Parar o motor ou a planta automaticamente |
| Fonte do limite | Quantis 95% e 99% de 26.291 leituras normais simuladas |
| Limitação | Aceleração derivada da vibração a 60 Hz; não é medição de acelerômetro |

## 5 Qualidade de dados e Circuit Breaker

| Regra | Resultado |
|---|---|
| Campo ausente, nulo ou não numérico | Bloquear alerta decisório |
| Valor fora do domínio físico | Bloquear alerta decisório |
| Unidade incompatível | Bloquear alerta decisório |
| Leitura atrasada mais de cinco minutos | Bloquear alerta decisório |
| Timestamp duplicado | Bloquear alerta decisório |
| Completude da janela menor que 90% | Bloquear alerta decisório |
| Modelo indisponível | Bloquear alerta decisório |
| Anomalia sem três janelas | Aguardar persistência e encaminhar para revisão |
| Confiança menor que 85% | Handoff humano |
| Divergência modelo–sensor | Handoff humano |

## 6 Monitoramento e revisão

- registrar cada alteração de threshold com versão, data, autor e justificativa;
- monitorar alertas bloqueados, falsos positivos e decisões rejeitadas;
- recalibrar os limites ao mudar sensor, planta, regime de carga ou base de dados;
- manter histórico das versões anteriores;
- exigir aprovação conjunta do Gestor de Planta e da Engenharia de Dados/IA.
