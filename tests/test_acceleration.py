import numpy as np
import pandas as pd

from src.acceleration import (
    calibrate_acceleration_thresholds,
    simulate_acceleration,
)


def sample_readings():
    return pd.DataFrame(
        {
            "motor_id": [1] * 8,
            "vibracao_mm_s": [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 9.0],
            "falha": [0, 0, 0, 0, 0, 0, 1, 1],
        }
    )


def test_acceleration_simulation_is_deterministic_and_non_negative():
    first = simulate_acceleration(sample_readings(), seed=17)
    second = simulate_acceleration(sample_readings(), seed=17)

    assert first["aceleracao_g"].tolist() == second["aceleracao_g"].tolist()
    assert first["aceleracao_g"].ge(0).all()


def test_acceleration_remains_strongly_correlated_with_vibration():
    simulated = simulate_acceleration(sample_readings(), seed=23, noise_std=0.01)

    correlation = simulated["vibracao_mm_s"].corr(simulated["aceleracao_g"])
    assert correlation > 0.99


def test_acceleration_conversion_matches_60_hz_formula_without_noise():
    readings = pd.DataFrame({"vibracao_mm_s": [6.0], "falha": [0]})

    simulated = simulate_acceleration(readings, frequency_hz=60.0, noise_std=0.0)

    expected = 2 * np.pi * 60 * 0.006 / 9.80665
    assert simulated.loc[0, "aceleracao_g"] == expected


def test_threshold_calibration_uses_only_normal_readings():
    simulated = simulate_acceleration(sample_readings(), seed=11, noise_std=0.0)

    metrics = calibrate_acceleration_thresholds(
        simulated,
        attention_quantile=0.75,
        critical_quantile=1.0,
    )

    normal_max = simulated.loc[simulated["falha"].eq(0), "aceleracao_g"].max()
    fault_min = simulated.loc[simulated["falha"].gt(0), "aceleracao_g"].min()
    assert metrics["critical_min"] == normal_max
    assert metrics["critical_min"] < fault_min
    assert metrics["normal_readings"] == 6


def test_threshold_calibration_rejects_invalid_quantile_order():
    simulated = simulate_acceleration(sample_readings(), seed=11)

    try:
        calibrate_acceleration_thresholds(
            simulated,
            attention_quantile=0.99,
            critical_quantile=0.95,
        )
    except ValueError as exc:
        assert "quantis" in str(exc)
    else:
        raise AssertionError("ordem inválida de quantis deveria falhar")
