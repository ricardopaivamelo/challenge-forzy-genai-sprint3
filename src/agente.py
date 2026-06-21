"""Agente conversacional com function calling — Sprint 2 GenAI (Challenge Forzy).

O usuário descreve as leituras de um motor em linguagem natural; o LLM decide chamar a
tool `prever_falha_motor`, que executa o modelo de ML treinado (modelo_falhas.joblib) e
devolve a classe prevista + probabilidades. O LLM então explica o diagnóstico.

Suporta OpenAI (gpt-4o-mini) ou Anthropic (Claude Haiku) — usa a key presente no .env.

Uso:
    python src/agente.py --demo     # roda os 3 cenários exigidos
    python src/agente.py            # chat interativo
"""
from pathlib import Path
import json
import os
import sys
import numpy as np
import pandas as pd
import joblib

HERE = Path(__file__).resolve().parent
SPRINT = HERE.parent

try:  # carga do .env é opcional (a tool funciona sem LLM)
    from dotenv import load_dotenv
    load_dotenv(SPRINT / ".env")
except ImportError:
    pass

# --------------------------------------------------------------------- a tool
_BUNDLE = None
FAIXA_NORMAL = {  # faixas nominais aproximadas (BANCO.md) p/ contextualizar desvios
    "rotacao_rpm": (1700, 1850),
    "vibracao_mm_s": (0, 3.5),
    "temperatura_c": (60, 75),
    "corrente_a": (10, 14),
}


def _load_model():
    global _BUNDLE
    if _BUNDLE is None:
        # Seguro: o .joblib é gerado pelo nosso próprio treino (src/train.py /
        # treinamento.ipynb), artefato local confiável — não vem de fonte externa.
        _BUNDLE = joblib.load(SPRINT / "models" / "modelo_falhas.joblib")
    return _BUNDLE


def prever_falha_motor(rotacao_rpm, vibracao_mm_s, temperatura_c, corrente_a) -> dict:
    """Roda o modelo sobre uma leitura instantânea e retorna diagnóstico estruturado."""
    b = _load_model()
    model, feats, tipos = b["model"], b["features"], b["tipos_falha"]
    valores = {"rotacao_rpm": float(rotacao_rpm), "vibracao_mm_s": float(vibracao_mm_s),
               "temperatura_c": float(temperatura_c), "corrente_a": float(corrente_a)}
    X = pd.DataFrame([valores])[feats]  # respeita a ordem e os nomes das features
    proba = model.predict_proba(X)[0]
    pred = int(model.classes_[int(np.argmax(proba))])
    probs = {tipos[int(c)]: round(float(p), 3) for c, p in zip(model.classes_, proba)}
    fora = []
    for f, v in valores.items():
        lo, hi = FAIXA_NORMAL[f]
        if v < lo:
            fora.append(f"{f}={v} abaixo do normal ({lo}-{hi})")
        elif v > hi:
            fora.append(f"{f}={v} acima do normal ({lo}-{hi})")
    return {
        "classe_prevista": tipos[pred],
        "codigo": pred,
        "probabilidades": probs,
        "confianca": round(float(max(proba)), 3),
        "sensores_fora_da_faixa": fora or ["todos dentro da faixa normal"],
        "importancia_global_features": b["feature_importances"],
    }


# ----------------------------------------------------------------- LLM config
SYSTEM = (
    "Você é um engenheiro de manutenção preditiva de motores elétricos industriais. "
    "Quando o usuário informar leituras de sensores (rotação, vibração, temperatura, "
    "corrente), use SEMPRE a ferramenta prever_falha_motor para obter o diagnóstico do "
    "modelo de ML — não chute. Depois explique em linguagem acessível: a classe de falha "
    "prevista, o nível de risco e quais sensores mais contribuíram, relacionando os valores "
    "fora da faixa normal ao tipo de falha. "
    "Sobre incerteza: cite a probabilidade da classe prevista; se a confiança for inferior a "
    "~85% ou houver outra classe com probabilidade relevante, deixe a incerteza EXPLÍCITA — "
    "diga claramente que o resultado não é conclusivo e cite a segunda hipótese mais provável "
    "com sua probabilidade, recomendando verificação adicional. Seja conciso e técnico."
)

_PARAMS = {
    "rotacao_rpm": {"type": "number", "description": "Rotação do eixo em RPM"},
    "vibracao_mm_s": {"type": "number", "description": "Vibração RMS no mancal em mm/s"},
    "temperatura_c": {"type": "number", "description": "Temperatura da carcaça em °C"},
    "corrente_a": {"type": "number", "description": "Corrente de linha em A"},
}
_REQUIRED = list(_PARAMS)
_DESC = "Prevê o tipo de falha de um motor a partir de uma leitura instantânea de sensores."


def _run_openai(user_msg, model="gpt-4o-mini"):
    from openai import OpenAI
    client = OpenAI()
    tools = [{"type": "function", "function": {
        "name": "prever_falha_motor", "description": _DESC,
        "parameters": {"type": "object", "properties": _PARAMS, "required": _REQUIRED}}}]
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_msg}]
    resp = client.chat.completions.create(model=model, messages=messages, tools=tools)
    msg = resp.choices[0].message
    if msg.tool_calls:
        messages.append(msg)
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = prever_falha_motor(**args)
            messages.append({"role": "tool", "tool_call_id": tc.id,
                             "content": json.dumps(result, ensure_ascii=False)})
        resp = client.chat.completions.create(model=model, messages=messages, tools=tools)
        msg = resp.choices[0].message
    return msg.content


def _run_anthropic(user_msg, model="claude-haiku-4-5"):
    import anthropic
    client = anthropic.Anthropic()
    tools = [{"name": "prever_falha_motor", "description": _DESC,
              "input_schema": {"type": "object", "properties": _PARAMS, "required": _REQUIRED}}]
    messages = [{"role": "user", "content": user_msg}]
    resp = client.messages.create(model=model, max_tokens=1024, system=SYSTEM,
                                  tools=tools, messages=messages)
    while resp.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                result = prever_falha_motor(**block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(result, ensure_ascii=False)})
        messages.append({"role": "user", "content": results})
        resp = client.messages.create(model=model, max_tokens=1024, system=SYSTEM,
                                      tools=tools, messages=messages)
    return "".join(b.text for b in resp.content if b.type == "text")


def responder(user_msg):
    if os.getenv("OPENAI_API_KEY"):
        return _run_openai(user_msg)
    if os.getenv("ANTHROPIC_API_KEY"):
        return _run_anthropic(user_msg)
    raise RuntimeError(
        "Nenhuma API key no .env. Defina OPENAI_API_KEY ou ANTHROPIC_API_KEY "
        f"em {SPRINT/'.env'} (veja .env.example).")


# --------------------------------------------------------------------- demo
CENARIOS = [
    ("Operação normal",
     "Tenho um motor com rotação 1780 RPM, vibração 2.1 mm/s, temperatura 67 °C e corrente 12.0 A. Como está?"),
    ("Falha clara (superaquecimento)",
     "Motor com vibração 3.0 mm/s, temperatura 96 °C, corrente 16.8 A e rotação 1775 RPM. Qual o diagnóstico?"),
    ("Leituras ambíguas",
     "Motor: rotação 1610 RPM, vibração 5.5 mm/s, temperatura 79 °C, corrente 15.0 A. O que pode ser?"),
]


def demo():
    for nome, msg in CENARIOS:
        print("\n" + "=" * 70)
        print(f"CENÁRIO: {nome}\nUsuário: {msg}\n" + "-" * 70)
        print("Agente:", responder(msg))


def interativo():
    print("Agente de diagnóstico de motores (digite 'sair' para encerrar).")
    while True:
        try:
            msg = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if msg.lower() in {"sair", "exit", "quit"}:
            break
        if msg:
            print("Agente:", responder(msg))


if __name__ == "__main__":
    demo() if "--demo" in sys.argv else interativo()
