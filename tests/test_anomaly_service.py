from pathlib import Path

from src.anomaly_service import build_agent_payload
from src.governance_contracts import load_metric_contracts
from src.governance_service import evaluate_governance


ROOT = Path(__file__).resolve().parents[1]


def test_agent_payload_reports_score_severity_and_dominant_sensor():
    payload = build_agent_payload(
        motor_id=7,
        timestamp="2026-01-01T12:00:00",
        score=0.40,
        threshold=0.20,
        persistent=True,
        sensor_errors={"vibracao_mm_s": 0.8, "corrente_a": 0.3},
    )

    assert payload["severity"] == "high"
    assert payload["persistent"] is True
    assert payload["dominant_sensors"][0] == "vibracao_mm_s"
    assert "inspeção" in payload["explanation"].lower()


def test_agent_payload_keeps_normal_reading_without_inspection_alert():
    payload = build_agent_payload(
        motor_id=2,
        timestamp="2026-01-01T12:00:00",
        score=0.10,
        threshold=0.20,
        persistent=False,
        sensor_errors={"temperatura_c": 0.1},
    )

    assert payload["severity"] == "normal"
    assert "dentro do baseline" in payload["explanation"].lower()


def test_agent_payload_embeds_governance_without_changing_model_facts():
    governance = evaluate_governance(
        motor_id=7,
        readings={
            "temperatura_c": 102.0,
            "vibracao_mm_s": 9.5,
            "aceleracao_g": 0.20,
        },
        units={
            "temperatura_c": "°C",
            "vibracao_mm_s": "mm/s",
            "aceleracao_g": "g",
        },
        timestamp="2026-08-31T12:00:00+00:00",
        now="2026-08-31T12:00:00+00:00",
        score=1.40,
        threshold=0.9513,
        persistent=True,
        classifier_confidence=0.95,
        completeness_ratio=1.0,
        duplicate_timestamp=False,
        model_available=True,
        contracts=load_metric_contracts(ROOT / "config" / "metric_contracts.json"),
    )

    payload = build_agent_payload(
        motor_id=7,
        timestamp="2026-08-31T12:00:00+00:00",
        score=1.40,
        threshold=0.9513,
        persistent=True,
        sensor_errors={"vibracao_mm_s": 0.8, "temperatura_c": 0.7},
        governance_decision=governance,
    )

    assert payload["anomaly_score"] == 1.40
    assert payload["threshold"] == 0.9513
    assert payload["governance"]["status"] == "alert"
    assert payload["governance"]["handoff"]["status"] == "pending"
