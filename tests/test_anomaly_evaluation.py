from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.anomaly_data import prepare_windows
from src.anomaly_evaluation import (
    binary_metrics,
    build_motor_ranking,
    build_sensor_ranking,
    compare_sprint2,
    evaluate_events,
    extract_fault_events,
)
from src.data_utils import load_leituras


def test_binary_metrics_match_hand_checked_confusion_matrix():
    result = binary_metrics(
        y_true=np.array([0, 0, 1, 1]),
        scores=np.array([0.1, 0.8, 0.9, 0.2]),
        threshold=0.5,
    )

    assert result["confusion_matrix"] == [[1, 1], [1, 1]]
    assert result["precision"] == pytest.approx(0.5)
    assert result["recall"] == pytest.approx(0.5)
    assert result["f1"] == pytest.approx(0.5)
    assert result["false_positive_rate"] == pytest.approx(0.5)


def test_extract_fault_events_splits_normal_gap_and_fault_class_change():
    readings = pd.DataFrame(
        {
            "motor_id": [1] * 8,
            "timestamp": pd.date_range("2026-01-01", periods=8, freq="min"),
            "falha": [0, 2, 2, 0, 2, 2, 3, 3],
        }
    )

    events = extract_fault_events(readings)

    assert events["fault_class"].tolist() == [2, 2, 3]
    assert events["duration_minutes"].tolist() == [2, 2, 2]
    assert events["start"].tolist() == [
        pd.Timestamp("2026-01-01 00:01:00"),
        pd.Timestamp("2026-01-01 00:04:00"),
        pd.Timestamp("2026-01-01 00:06:00"),
    ]


def test_event_evaluation_reports_positive_lead_time_for_early_alert():
    events = pd.DataFrame(
        {
            "event_id": [1],
            "motor_id": [7],
            "fault_class": [2],
            "start": [pd.Timestamp("2026-01-01 00:10:00")],
            "end": [pd.Timestamp("2026-01-01 00:15:00")],
            "duration_minutes": [6],
        }
    )
    scored = pd.DataFrame(
        {
            "motor_id": [7, 7, 7],
            "timestamp": pd.to_datetime(
                ["2026-01-01 00:00", "2026-01-01 00:05", "2026-01-01 00:10"]
            ),
            "autoencoder_persistent": [False, True, True],
        }
    )

    details, summary = evaluate_events(events, scored, "autoencoder")

    assert bool(details.loc[0, "detected"])
    assert details.loc[0, "lead_minutes"] == pytest.approx(5.0)
    assert summary["event_recall"] == pytest.approx(1.0)
    assert summary["median_lead_minutes"] == pytest.approx(5.0)


def test_rankings_use_only_requested_partition_and_alerted_sensor_errors():
    scored = pd.DataFrame(
        {
            "motor_id": [1, 1, 2, 2, 3],
            "partition": ["test", "test", "test", "test", "train"],
            "y_anomaly": [0, 1, 0, 1, 1],
            "autoencoder_score": [0.1, 2.0, 0.2, 1.0, 9.0],
            "autoencoder_alert": [False, True, False, True, True],
            "autoencoder_persistent": [False, True, False, False, True],
            "ae_error_rotacao_rpm": [0.1, 0.2, 0.1, 0.1, 9.0],
            "ae_error_vibracao_mm_s": [0.1, 0.9, 0.1, 0.2, 9.0],
            "ae_error_temperatura_c": [0.1, 0.3, 0.1, 0.8, 9.0],
            "ae_error_corrente_a": [0.1, 0.4, 0.1, 0.3, 9.0],
        }
    )

    motors = build_motor_ranking(scored, "autoencoder", partition="test")
    sensors = build_sensor_ranking(scored, partition="test")

    assert motors["motor_id"].tolist() == [1, 2]
    assert motors.loc[0, "max_score"] == pytest.approx(2.0)
    assert sensors.iloc[0]["sensor"] in {"vibracao_mm_s", "temperatura_c"}
    assert set(sensors["dominant_alert_count"]) == {0, 1}


def test_sprint2_comparison_preserves_window_endpoints():
    readings = load_leituras(join_motores=False)
    prepared = prepare_windows(readings)
    endpoints = prepared.metadata.query("partition == 'test'").head(25).copy()

    compared = compare_sprint2(
        readings, endpoints, model_path="models/modelo_falhas.joblib"
    )

    assert compared[["motor_id", "timestamp"]].equals(
        endpoints[["motor_id", "timestamp"]].reset_index(drop=True)
    )
    assert compared["sprint2_score"].between(0, 1).all()
    assert compared["sprint2_alert"].dtype == bool
