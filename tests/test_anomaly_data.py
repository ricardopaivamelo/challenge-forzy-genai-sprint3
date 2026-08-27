from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.data_utils import FEATURES, load_leituras
from src.anomaly_data import (
    SplitConfig,
    WindowConfig,
    assign_partition,
    build_windows,
    fit_motor_baselines,
    normalize_by_motor,
    prepare_windows,
)


def make_readings(
    motor_id: int = 4,
    periods: int = 40,
    *,
    gap_after: int | None = None,
    constant: bool = False,
) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-01", periods=periods, freq="min")
    if gap_after is not None:
        timestamps = timestamps.to_series(index=range(periods))
        timestamps.loc[gap_after + 1 :] += pd.Timedelta(minutes=5)
        timestamps = pd.DatetimeIndex(timestamps)
    base = np.zeros(periods) if constant else np.arange(periods, dtype=float)
    return pd.DataFrame(
        {
            "motor_id": motor_id,
            "timestamp": timestamps,
            "rotacao_rpm": 1_000 + base,
            "vibracao_mm_s": 2 + base * 0.1,
            "temperatura_c": 40 + base * 0.2,
            "corrente_a": 10 + base * 0.05,
            "falha": np.zeros(periods, dtype=int),
        }
    )


def test_assign_partition_keeps_motors_disjoint_and_matches_sprint2_test():
    assigned = assign_partition(load_leituras(join_motores=False))

    assert assigned.groupby("motor_id")["partition"].nunique().eq(1).all()
    assert set(assigned.query("partition == 'validation'")["motor_id"]) == {3, 8, 13}
    assert set(assigned.query("partition == 'test'")["motor_id"]) == {1, 2, 10, 15, 16}
    assert set(assigned.query("partition == 'train'")["motor_id"]) == {
        4, 5, 6, 7, 9, 11, 12, 14, 17, 18, 19, 20
    }


def test_motor_baseline_uses_first_30_rows_and_protects_zero_iqr():
    readings = make_readings(periods=35, constant=True)

    baselines = fit_motor_baselines(readings, calibration_size=30, epsilon=1e-6)

    assert baselines.median.loc[4, "rotacao_rpm"] == pytest.approx(1_000)
    assert baselines.iqr.loc[4, "rotacao_rpm"] == pytest.approx(1e-6)


def test_normalization_centers_calibration_median_per_motor():
    readings = pd.concat([make_readings(4), make_readings(5)], ignore_index=True)
    readings.loc[readings.motor_id == 5, FEATURES] += [300, 2, 15, 4]
    baselines = fit_motor_baselines(readings, calibration_size=30)

    normalized = normalize_by_motor(readings, baselines)
    calibration = normalized.groupby("motor_id", sort=False).head(30)

    assert np.allclose(calibration.groupby("motor_id")[FEATURES].median(), 0.0)


def test_build_windows_never_crosses_a_time_gap():
    readings = make_readings(periods=40, gap_after=19)
    assigned = assign_partition(readings)
    baselines = fit_motor_baselines(assigned, calibration_size=10)
    normalized = normalize_by_motor(assigned, baselines)

    windows = build_windows(
        normalized,
        WindowConfig(window_size=10, stride=5, calibration_size=10, guard_size=5),
    )

    assert windows.sequences.shape[1:] == (10, 4)
    assert windows.summaries.shape[1] == 24
    assert len(windows.metadata) == 6
    assert windows.metadata["contiguous"].all()


def test_prepare_windows_marks_fault_guard_as_ineligible_for_training():
    readings = make_readings(periods=50)
    readings.loc[35:39, "falha"] = 2

    prepared = prepare_windows(
        readings,
        split_config=SplitConfig(validation_motors=(), test_motors=()),
        window_config=WindowConfig(
            window_size=10, stride=1, calibration_size=10, guard_size=5
        ),
    )

    endpoints = prepared.metadata.set_index("end_position")
    assert bool(endpoints.loc[25, "train_eligible"])
    assert not bool(endpoints.loc[30, "train_eligible"])
    assert not bool(endpoints.loc[39, "train_eligible"])
    assert prepared.feature_names[0] == "rotacao_rpm_mean"
    assert prepared.feature_names[-1] == "corrente_a_slope"
