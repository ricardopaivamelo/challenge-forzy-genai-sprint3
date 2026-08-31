"""Simulação auditável de aceleração para o protótipo acadêmico da Forzy."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


STANDARD_GRAVITY_M_S2 = 9.80665


def simulate_acceleration(
    readings: pd.DataFrame,
    *,
    seed: int = 42,
    frequency_hz: float = 60.0,
    noise_std: float = 0.03,
) -> pd.DataFrame:
    """Adiciona aceleração equivalente em g a partir da vibração RMS.

    A conversão assume uma componente senoidal dominante em ``frequency_hz`` e aplica
    ruído multiplicativo determinístico. É uma aproximação para demonstração, não uma
    medição de acelerômetro nem um dado industrial real.
    """

    if "vibracao_mm_s" not in readings:
        raise ValueError("coluna vibracao_mm_s é obrigatória")
    if frequency_hz <= 0 or not math.isfinite(frequency_hz):
        raise ValueError("frequency_hz deve ser positivo e finito")
    if noise_std < 0 or not math.isfinite(noise_std):
        raise ValueError("noise_std deve ser não negativo e finito")

    vibration = pd.to_numeric(readings["vibracao_mm_s"], errors="raise").to_numpy(float)
    if not np.isfinite(vibration).all() or (vibration < 0).any():
        raise ValueError("vibracao_mm_s deve conter valores finitos e não negativos")
    rng = np.random.default_rng(seed)
    noise = rng.normal(loc=0.0, scale=noise_std, size=len(readings))
    velocity_m_s = vibration / 1000.0
    acceleration_g = 2 * np.pi * frequency_hz * velocity_m_s / STANDARD_GRAVITY_M_S2
    acceleration_g = np.clip(acceleration_g * (1.0 + noise), a_min=0.0, a_max=None)

    result = readings.copy()
    result["aceleracao_g"] = acceleration_g
    return result


def calibrate_acceleration_thresholds(
    readings: pd.DataFrame,
    *,
    attention_quantile: float = 0.95,
    critical_quantile: float = 0.99,
) -> dict[str, object]:
    """Calcula limiares somente sobre leituras rotuladas como normais."""

    if not 0 < attention_quantile < critical_quantile <= 1:
        raise ValueError("quantis devem obedecer 0 < atenção < crítico <= 1")
    required = {"falha", "aceleracao_g"}
    missing = required.difference(readings.columns)
    if missing:
        raise ValueError(f"colunas ausentes: {sorted(missing)}")
    normal = readings.loc[readings["falha"].eq(0), "aceleracao_g"].dropna()
    if normal.empty:
        raise ValueError("não há leituras normais para calibrar aceleração")
    return {
        "attention_min": float(normal.quantile(attention_quantile)),
        "critical_min": float(normal.quantile(critical_quantile)),
        "attention_quantile": attention_quantile,
        "critical_quantile": critical_quantile,
        "normal_readings": int(len(normal)),
        "normal_min": float(normal.min()),
        "normal_max": float(normal.max()),
        "method": "sinusoidal_60hz_from_vibration_with_seeded_noise",
        "limitation": "simulated_acceleration_not_industrial_measurement",
    }
