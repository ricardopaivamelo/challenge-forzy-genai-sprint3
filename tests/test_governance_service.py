from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.governance_contracts import load_metric_contracts
from src.governance_service import evaluate_governance


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = load_metric_contracts(ROOT / "config" / "metric_contracts.json")
NOW = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
NORMAL = {
    "temperatura_c": 70.0,
    "vibracao_mm_s": 2.0,
    "aceleracao_g": 0.08,
}
UNITS = {
    "temperatura_c": "°C",
    "vibracao_mm_s": "mm/s",
    "aceleracao_g": "g",
}


def evaluate(**overrides):
    kwargs = {
        "motor_id": 7,
        "readings": NORMAL,
        "units": UNITS,
        "timestamp": NOW,
        "now": NOW,
        "score": 0.50,
        "threshold": 0.9513,
        "persistent": False,
        "classifier_confidence": 0.95,
        "completeness_ratio": 1.0,
        "duplicate_timestamp": False,
        "model_available": True,
        "contracts": CONTRACTS,
    }
    kwargs.update(overrides)
    return evaluate_governance(**kwargs)


def test_normal_readings_are_logged_without_handoff():
    decision = evaluate()

    assert decision.status == "normal"
    assert decision.circuit_breaker_open is False
    assert decision.requires_human is False


def test_physical_attention_without_model_alert_keeps_monitoring():
    decision = evaluate(readings={**NORMAL, "temperatura_c": 90.0})

    assert decision.status == "attention"
    assert decision.sensor_states["temperatura_c"] == "attention"
    assert "monitoramento" in decision.automatic_action.lower()


def test_persistent_model_anomaly_with_physical_evidence_creates_handoff():
    decision = evaluate(
        readings={**NORMAL, "vibracao_mm_s": 9.5, "aceleracao_g": 0.37},
        score=1.40,
        persistent=True,
    )

    assert decision.status == "alert"
    assert decision.circuit_breaker_open is False
    assert decision.requires_human is True
    assert decision.handoff["status"] == "pending"
    assert decision.handoff["recipient"] == "Engenheiro de Manutenção"


@pytest.mark.parametrize(
    ("overrides", "reason_fragment"),
    [
        ({"readings": {"temperatura_c": 70, "vibracao_mm_s": 2}}, "ausente"),
        ({"readings": {**NORMAL, "temperatura_c": "inválido"}}, "não numérico"),
        ({"timestamp": NOW - timedelta(minutes=6)}, "desatualizada"),
        ({"duplicate_timestamp": True}, "duplicado"),
        ({"completeness_ratio": 0.89}, "completude"),
        ({"units": {**UNITS, "aceleracao_g": "m/s²"}}, "unidade"),
        ({"model_available": False}, "modelo"),
    ],
)
def test_data_or_model_fault_opens_circuit_breaker(overrides, reason_fragment):
    decision = evaluate(**overrides)

    assert decision.status == "blocked"
    assert decision.circuit_breaker_open is True
    assert any(reason_fragment in reason.lower() for reason in decision.breaker_reasons)
    assert decision.requires_human is True


def test_non_persistent_model_anomaly_is_blocked_before_alert():
    decision = evaluate(
        readings={**NORMAL, "vibracao_mm_s": 6.5},
        score=1.10,
        persistent=False,
    )

    assert decision.status == "blocked"
    assert "persistência" in " ".join(decision.breaker_reasons).lower()


def test_low_classifier_confidence_blocks_candidate_alert():
    decision = evaluate(
        readings={**NORMAL, "temperatura_c": 101.0},
        score=1.20,
        persistent=True,
        classifier_confidence=0.84,
    )

    assert decision.status == "blocked"
    assert "confiança" in " ".join(decision.breaker_reasons).lower()


def test_model_sensor_divergence_blocks_candidate_alert():
    decision = evaluate(score=1.20, persistent=True)

    assert decision.status == "blocked"
    assert "divergência" in " ".join(decision.breaker_reasons).lower()


def test_invalid_threshold_is_rejected_before_decision():
    with pytest.raises(ValueError, match="threshold"):
        evaluate(threshold=0)
