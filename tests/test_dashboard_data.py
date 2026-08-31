from pathlib import Path

from datetime import datetime, timezone

from src.dashboard_data import build_contract_rows, build_handoff_record
from src.governance_contracts import load_metric_contracts


ROOT = Path(__file__).resolve().parents[1]


def test_contract_table_normalizes_mixed_sensor_values_for_arrow():
    contracts = load_metric_contracts(ROOT / "config" / "metric_contracts.json")

    rows = build_contract_rows(
        contracts=contracts,
        readings={
            "temperatura_c": "sensor_error",
            "vibracao_mm_s": 9.8,
            "aceleracao_g": 0.21,
        },
        sensor_states={
            "vibracao_mm_s": "critical",
            "aceleracao_g": "critical",
        },
    )

    assert [row["Valor"] for row in rows] == ["sensor_error", "9.8", "0.21"]
    assert all(isinstance(row["Valor"], str) for row in rows)


def test_handoff_record_preserves_alert_context_for_audit():
    recorded_at = datetime(2026, 8, 31, 12, 30, tzinfo=timezone.utc)

    record = build_handoff_record(
        alert_id="ALT-MTR-017-20260831T123000Z",
        motor_id=17,
        scenario_name="Handoff por baixa confiança",
        decision="Validado",
        justification="Obra próxima alterou a vibração.",
        recorded_at=recorded_at,
        readings={"temperatura_c": 84.0, "vibracao_mm_s": 9.4},
        anomaly_score=1.1,
        model_threshold=0.9513,
        classifier_confidence=0.72,
        minimum_confidence=0.85,
        breaker_reasons=["Confiança 72,0% abaixo do mínimo de 85,0%."],
        contract_versions={"temperatura_c": "1.0", "vibracao_mm_s": "1.0"},
    )

    assert record["alert_id"] == "ALT-MTR-017-20260831T123000Z"
    assert record["motor_id"] == 17
    assert record["recorded_at"] == "2026-08-31T12:30:00+00:00"
    assert record["decision"] == "Validado"
    assert record["justification"] == "Obra próxima alterou a vibração."
    assert record["evidence"]["classifier_confidence"] == 0.72
    assert record["evidence"]["minimum_confidence"] == 0.85
    assert record["evidence"]["readings"]["vibracao_mm_s"] == 9.4
    assert record["evidence"]["contract_versions"]["temperatura_c"] == "1.0"
