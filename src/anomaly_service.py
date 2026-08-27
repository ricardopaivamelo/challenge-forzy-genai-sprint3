"""Contrato determinístico para futura integração com agente conversacional."""

from __future__ import annotations

from datetime import datetime
from typing import Mapping

import pandas as pd


def build_agent_payload(
    *,
    motor_id: int,
    timestamp: str | datetime | pd.Timestamp,
    score: float,
    threshold: float,
    persistent: bool,
    sensor_errors: Mapping[str, float],
) -> dict[str, object]:
    """Converte um resultado técnico em payload factual e explicável."""

    if threshold <= 0:
        raise ValueError("threshold deve ser positivo")
    ratio = float(score / threshold)
    if ratio < 1:
        severity = "normal"
    elif ratio < 1.5 and not persistent:
        severity = "attention"
    else:
        severity = "high"
    ranked_sensors = sorted(sensor_errors, key=sensor_errors.get, reverse=True)
    dominant_sensors = ranked_sensors[:2]
    if severity == "normal":
        explanation = "Comportamento dentro do baseline operacional do motor."
    else:
        persistence_text = "persistente" if persistent else "pontual"
        sensor_text = ", ".join(dominant_sensors) or "sensores não informados"
        explanation = (
            f"Desvio {persistence_text} acima do baseline, com maior erro em "
            f"{sensor_text}. Recomenda-se inspeção técnica; o alerta não comprova a causa."
        )
    return {
        "motor_id": int(motor_id),
        "timestamp": pd.Timestamp(timestamp).isoformat(),
        "anomaly_score": float(score),
        "threshold": float(threshold),
        "score_ratio": ratio,
        "severity": severity,
        "persistent": bool(persistent),
        "dominant_sensors": dominant_sensors,
        "sensor_errors": {name: float(value) for name, value in sensor_errors.items()},
        "explanation": explanation,
    }

