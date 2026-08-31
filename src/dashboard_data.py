"""Adaptação de dados técnicos para apresentação estável no dashboard."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from src.governance_contracts import MetricContract


def build_contract_rows(
    *,
    contracts: Mapping[str, MetricContract],
    readings: Mapping[str, object],
    sensor_states: Mapping[str, str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for field, contract in contracts.items():
        rows.append(
            {
                "Métrica": contract.label,
                "Valor": str(readings.get(field)),
                "Unidade": contract.unit,
                "Atenção": contract.attention_min,
                "Crítico": contract.critical_min,
                "Estado": sensor_states.get(field, "invalid"),
                "Versão": contract.version,
            }
        )
    return rows


def build_handoff_record(
    *,
    alert_id: str,
    motor_id: int,
    scenario_name: str,
    decision: str,
    justification: str,
    recorded_at: datetime,
    readings: Mapping[str, object],
    anomaly_score: float,
    model_threshold: float,
    classifier_confidence: float | None,
    minimum_confidence: float,
    breaker_reasons: list[str] | tuple[str, ...],
    contract_versions: Mapping[str, str],
) -> dict[str, object]:
    """Cria o registro autocontido da validação humana para auditoria da demo."""

    timestamp = recorded_at
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    else:
        timestamp = timestamp.astimezone(timezone.utc)

    return {
        "alert_id": alert_id,
        "motor_id": int(motor_id),
        "scenario": scenario_name,
        "recorded_at": timestamp.isoformat(),
        "decision": decision,
        "justification": justification,
        "evidence": {
            "readings": dict(readings),
            "anomaly_score": float(anomaly_score),
            "model_threshold": float(model_threshold),
            "classifier_confidence": classifier_confidence,
            "minimum_confidence": float(minimum_confidence),
            "breaker_reasons": list(breaker_reasons),
            "contract_versions": dict(contract_versions),
        },
    }
