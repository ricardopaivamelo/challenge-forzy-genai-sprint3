from __future__ import annotations

import numpy as np
import pandas as pd

from src.anomaly_data import PreparedWindows, WindowConfig
from src.anomaly_models import (
    apply_threshold_and_persistence,
    fit_anomaly_models,
    score_anomaly_models,
    statistical_scores,
)


def make_prepared_windows() -> PreparedWindows:
    rng = np.random.default_rng(42)
    n_train, n_validation, n_test = 90, 45, 30
    total = n_train + n_validation + n_test
    sequences = rng.normal(0, 0.25, size=(total, 30, 4))
    summaries = rng.normal(0, 0.25, size=(total, 24))
    partitions = np.repeat(
        ["train", "validation", "test"],
        [n_train, n_validation, n_test],
    )
    y = np.zeros(total, dtype=int)
    y[-10:] = 1
    sequences[-10:, :, 1] += 5
    summaries[-10:, 6:12] += 5
    metadata = pd.DataFrame(
        {
            "motor_id": np.concatenate(
                [np.repeat(4, n_train), np.repeat(3, n_validation), np.repeat(1, n_test)]
            ),
            "timestamp": pd.date_range("2026-01-01", periods=total, freq="5min"),
            "end_position": np.arange(total),
            "falha": y,
            "y_anomaly": y,
            "partition": partitions,
            "all_normal": y == 0,
            "guard_clean": y == 0,
            "train_eligible": y == 0,
            "contiguous": True,
        }
    )
    return PreparedWindows(
        sequences=sequences,
        summaries=summaries,
        metadata=metadata,
        feature_names=[f"summary_{index}" for index in range(24)],
        baselines=None,
        config=WindowConfig(),
    )


def test_statistical_score_increases_for_large_sensor_deviation():
    normal = np.zeros((1, 30, 4))
    anomaly = normal.copy()
    anomaly[:, :, 1] = 8.0

    assert statistical_scores(anomaly)[0] > statistical_scores(normal)[0]


def test_fit_uses_only_train_windows_and_validation_normals_for_threshold():
    prepared = make_prepared_windows()

    bundle = fit_anomaly_models(prepared)

    assert bundle.threshold_source == "validation_normal_guard_clean"
    assert bundle.fit_counts == {"train": 90, "validation_threshold": 45}
    assert set(bundle.thresholds) == {"statistical", "isolation_forest", "autoencoder"}
    assert all(np.isfinite(list(bundle.thresholds.values())))


def test_scoring_returns_sensor_errors_and_higher_autoencoder_score_for_shift():
    prepared = make_prepared_windows()
    bundle = fit_anomaly_models(prepared)

    scored = score_anomaly_models(prepared, bundle)

    assert all(f"ae_error_{feature}" in scored for feature in bundle.sensor_names)
    normal_mean = scored.loc[scored.y_anomaly == 0, "autoencoder_score"].mean()
    anomaly_mean = scored.loc[scored.y_anomaly == 1, "autoencoder_score"].mean()
    assert anomaly_mean > normal_mean
    shifted = scored.loc[scored.y_anomaly == 1]
    assert shifted["ae_error_vibracao_mm_s"].mean() > shifted["ae_error_corrente_a"].mean()


def test_persistence_requires_three_consecutive_alerts_per_motor():
    scores = np.array([0.2, 0.8, 0.9, 1.0, 0.9, 1.1, 1.2])
    motor_ids = np.array([1, 1, 1, 1, 2, 2, 2])

    alerts, persistent = apply_threshold_and_persistence(
        scores, threshold=0.5, motor_ids=motor_ids, min_consecutive=3
    )

    assert alerts.tolist() == [False, True, True, True, True, True, True]
    assert persistent.tolist() == [False, False, False, True, False, False, True]
