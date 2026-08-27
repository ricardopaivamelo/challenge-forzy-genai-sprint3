from src.anomaly_service import build_agent_payload


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

