# Demonstração do Agente — Sprint 2 GenAI (Challenge Forzy)

Evidência de execução do agente conversacional com *function calling*.

- **Provider / modelo:** OpenAI `gpt-4o-mini`
- **Tool registrada:** `prever_falha_motor(rotacao_rpm, vibracao_mm_s, temperatura_c, corrente_a)` → executa `models/modelo_falhas.joblib`
- **Gerado em:** 2026-06-21 15:17
- **Reproduzir:** `python src/agente.py --demo`

Fluxo: o usuário descreve as leituras em linguagem natural → o LLM decide chamar a tool → a tool roda o modelo de ML e retorna classe + probabilidades → o LLM explica o diagnóstico (classe, risco, sensores que pesaram e incerteza).

```text

======================================================================
CENÁRIO: Operação normal
Usuário: Tenho um motor com rotação 1780 RPM, vibração 2.1 mm/s, temperatura 67 °C e corrente 12.0 A. Como está?
----------------------------------------------------------------------
Agente: O diagnóstico para o motor indica que ele está em estado **normal**. A probabilidade de que o motor esteja em condição normal é de **100%**, o que significa que a previsão é bastante confiável.

Os sensores utilizados indicam os seguintes dados:
- **Rotação**: 1780 RPM (dentro da faixa normal)
- **Vibração**: 2.1 mm/s (dentro da faixa normal)
- **Temperatura**: 67 °C (dentro da faixa normal)
- **Corrente**: 12.0 A (dentro da faixa normal)

Nenhum sensor apresentou leituras fora da faixa normal, e todos contribuíram para essa avaliação. A importância dos sensores na avaliação foi:
- Vibração: 36.55%
- Rotação: 26.28%
- Temperatura: 22.37%
- Corrente: 14.8%

Portanto, o motor está operando de forma estável e não apresenta indicativos de falha.

======================================================================
CENÁRIO: Falha clara (superaquecimento)
Usuário: Motor com vibração 3.0 mm/s, temperatura 96 °C, corrente 16.8 A e rotação 1775 RPM. Qual o diagnóstico?
----------------------------------------------------------------------
Agente: O diagnóstico para o motor é **Superaquecimento** com uma probabilidade de 98%. Isso indica um alto nível de confiança no resultado.

**Nível de Risco:** Alto. O superaquecimento pode levar a danos significativos e falhas mais sérias se não for tratado.

**Sensores que mais contribuíram para o diagnóstico:**
1. **Temperatura:** A temperatura da carcaça está em 96 °C, que está acima da faixa ideal de 60-75 °C.
2. **Corrente:** A corrente está em 16.8 A, também acima do normal (10-14 A).

Esses dois fatores são críticos para o diagnóstico de superaquecimento, pois indicam que o motor pode estar sobrecarregado ou com algum problema que impede a dissipação adequada de calor. Recomendo a verificação imediata do sistema de refrigeração e a carga aplicada ao motor.

======================================================================
CENÁRIO: Leituras ambíguas
Usuário: Motor: rotação 1610 RPM, vibração 5.5 mm/s, temperatura 79 °C, corrente 15.0 A. O que pode ser?
----------------------------------------------------------------------
Agente: O motor está apresentando uma **falha mecânica**. A probabilidade dessa falha ser a causa principal é de **72.3%**, o que indica um risco significativo.

### Detalhes do Diagnóstico:
- **Classe Previstada:** Falha mecânica
- **Nível de Risco:** Alto (72.3% de probabilidade)

### Sensores fora da faixa normal:
1. **Rotação:** 1610 RPM (abaixo do normal: 1700-1850)
2. **Vibração:** 5.5 mm/s (acima do normal: 0-3.5)
3. **Temperatura:** 79 °C (acima do normal: 60-75)
4. **Corrente:** 15.0 A (acima do normal: 10-14)

### Contribuição dos Sensores:
- O sensor de **vibração** (5.5 mm/s) foi o que mais contribuiu para o diagnóstico, com uma importância global de **36.55%**.
- A **rotaciona** (1610 RPM) também é relevante, contribuindo com **26.28%**.

Esses valores indicam que a condição do motor está comprometida, especialmente a vibração elevada e a temperatura alta, que sugerem problemas mecânicos.

### Incerteza:
Embora a falha mecânica seja a mais provável, a confiança de 72.3% não é conclusiva. A segunda hipótese mais provável envolve **superaquecimento**, com uma probabilidade de **8%**. Recomendo uma verificação adicional para confirmar a situação do motor e prevenir danos maiores.
```
