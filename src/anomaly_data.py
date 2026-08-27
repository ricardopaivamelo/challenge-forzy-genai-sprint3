"""Preparação temporal sem vazamento para detecção de anomalias.

As leituras são calibradas por motor, separadas por ativo e transformadas em
janelas de 30 minutos. Rótulos são usados apenas para curar treino/validação e
avaliar; nunca são apresentados como alvo aos detectores de anomalia.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.data_utils import FEATURES


@dataclass(frozen=True)
class SplitConfig:
    """Partição fixa por motor, compatível com o teste da Sprint 2."""

    validation_motors: tuple[int, ...] = (3, 8, 13)
    test_motors: tuple[int, ...] = (1, 2, 10, 15, 16)


@dataclass(frozen=True)
class WindowConfig:
    """Configuração temporal do baseline e das janelas."""

    window_size: int = 30
    stride: int = 5
    calibration_size: int = 30
    guard_size: int = 30
    epsilon: float = 1e-6


@dataclass
class MotorBaselines:
    """Mediana e IQR calculados no período inicial de cada motor."""

    median: pd.DataFrame
    iqr: pd.DataFrame
    calibration_size: int


@dataclass
class PreparedWindows:
    """Representações temporais e metadados alinhados por janela."""

    sequences: np.ndarray
    summaries: np.ndarray
    metadata: pd.DataFrame
    feature_names: list[str]
    baselines: MotorBaselines | None
    config: WindowConfig


def _validate_split(split_config: SplitConfig) -> None:
    validation = set(split_config.validation_motors)
    test = set(split_config.test_motors)
    overlap = validation & test
    if overlap:
        raise ValueError(f"Motores repetidos em validação e teste: {sorted(overlap)}")


def assign_partition(
    df: pd.DataFrame, split_config: SplitConfig = SplitConfig()
) -> pd.DataFrame:
    """Anexa `partition` sem dividir leituras do mesmo motor."""

    _validate_split(split_config)
    assigned = df.copy()
    validation = set(split_config.validation_motors)
    test = set(split_config.test_motors)
    assigned["partition"] = np.select(
        [assigned["motor_id"].isin(validation), assigned["motor_id"].isin(test)],
        ["validation", "test"],
        default="train",
    )
    return assigned


def fit_motor_baselines(
    df: pd.DataFrame,
    calibration_size: int = 30,
    epsilon: float = 1e-6,
) -> MotorBaselines:
    """Calcula mediana/IQR usando somente as primeiras leituras de cada motor."""

    if calibration_size <= 0:
        raise ValueError("calibration_size deve ser positivo")
    ordered = df.sort_values(["motor_id", "timestamp"])
    counts = ordered.groupby("motor_id").size()
    short = counts[counts < calibration_size]
    if not short.empty:
        raise ValueError(
            "Motores sem leituras suficientes para calibração: "
            f"{short.to_dict()}"
        )
    calibration = ordered.groupby("motor_id", sort=True).head(calibration_size)
    grouped = calibration.groupby("motor_id")[FEATURES]
    median = grouped.median()
    iqr = grouped.quantile(0.75) - grouped.quantile(0.25)
    iqr = iqr.clip(lower=epsilon)
    return MotorBaselines(median=median, iqr=iqr, calibration_size=calibration_size)


def normalize_by_motor(
    df: pd.DataFrame, baselines: MotorBaselines
) -> pd.DataFrame:
    """Substitui os sensores por desvios robustos relativos ao próprio motor."""

    normalized = df.copy()
    unknown = set(normalized["motor_id"].unique()) - set(baselines.median.index)
    if unknown:
        raise ValueError(f"Motores sem baseline: {sorted(unknown)}")
    for feature in FEATURES:
        medians = normalized["motor_id"].map(baselines.median[feature])
        iqrs = normalized["motor_id"].map(baselines.iqr[feature])
        normalized[feature] = (normalized[feature] - medians) / iqrs
    return normalized


def _guard_clean(faults: np.ndarray, guard_size: int) -> np.ndarray:
    """Marca posições que não estão em nem próximas de falhas rotuladas."""

    clean = np.ones(len(faults), dtype=bool)
    for position in np.flatnonzero(faults > 0):
        start = max(0, position - guard_size)
        stop = min(len(faults), position + guard_size + 1)
        clean[start:stop] = False
    return clean


def _summary_feature_names() -> list[str]:
    stats = ("mean", "std", "min", "max", "last", "slope")
    return [f"{feature}_{stat}" for feature in FEATURES for stat in stats]


def _summarize_sequence(sequence: np.ndarray) -> np.ndarray:
    x = np.arange(sequence.shape[0], dtype=float)
    centered_x = x - x.mean()
    denominator = float(np.dot(centered_x, centered_x))
    values: list[float] = []
    for feature_index in range(sequence.shape[1]):
        sensor = sequence[:, feature_index]
        slope = float(np.dot(centered_x, sensor - sensor.mean()) / denominator)
        values.extend(
            [
                float(sensor.mean()),
                float(sensor.std(ddof=0)),
                float(sensor.min()),
                float(sensor.max()),
                float(sensor[-1]),
                slope,
            ]
        )
    return np.asarray(values, dtype=float)


def build_windows(
    normalized_df: pd.DataFrame,
    config: WindowConfig = WindowConfig(),
) -> PreparedWindows:
    """Cria janelas contíguas sem cruzar motores ou lacunas temporais."""

    if config.window_size < 2:
        raise ValueError("window_size deve ser pelo menos 2")
    if config.stride <= 0:
        raise ValueError("stride deve ser positivo")
    required = {"motor_id", "timestamp", "falha", "partition", *FEATURES}
    missing = required - set(normalized_df.columns)
    if missing:
        raise ValueError(f"Colunas ausentes para criar janelas: {sorted(missing)}")

    sequences: list[np.ndarray] = []
    summaries: list[np.ndarray] = []
    metadata: list[dict[str, object]] = []

    for motor_id, raw_group in normalized_df.groupby("motor_id", sort=True):
        group = raw_group.sort_values("timestamp").reset_index(drop=True)
        timestamps = pd.to_datetime(group["timestamp"])
        sensor_values = group[FEATURES].to_numpy(dtype=float)
        faults = group["falha"].to_numpy(dtype=int)
        guard_clean = _guard_clean(faults, config.guard_size)

        for start in range(0, len(group) - config.window_size + 1, config.stride):
            stop = start + config.window_size
            time_slice = timestamps.iloc[start:stop]
            deltas = time_slice.diff().dropna()
            contiguous = bool((deltas == pd.Timedelta(minutes=1)).all())
            if not contiguous:
                continue
            sequence = sensor_values[start:stop]
            endpoint = stop - 1
            all_normal = bool((faults[start:stop] == 0).all())
            clean_window = bool(guard_clean[start:stop].all())
            sequences.append(sequence)
            summaries.append(_summarize_sequence(sequence))
            metadata.append(
                {
                    "motor_id": int(motor_id),
                    "timestamp": timestamps.iloc[endpoint],
                    "end_position": int(endpoint),
                    "falha": int(faults[endpoint]),
                    "y_anomaly": int(faults[endpoint] > 0),
                    "partition": str(group["partition"].iloc[endpoint]),
                    "all_normal": all_normal,
                    "guard_clean": clean_window,
                    "train_eligible": all_normal and clean_window,
                    "contiguous": True,
                }
            )

    sequence_array = np.asarray(sequences, dtype=float)
    summary_array = np.asarray(summaries, dtype=float)
    if not sequences:
        sequence_array = np.empty((0, config.window_size, len(FEATURES)))
        summary_array = np.empty((0, len(_summary_feature_names())))
    return PreparedWindows(
        sequences=sequence_array,
        summaries=summary_array,
        metadata=pd.DataFrame(metadata),
        feature_names=_summary_feature_names(),
        baselines=None,
        config=config,
    )


def prepare_windows(
    df: pd.DataFrame,
    split_config: SplitConfig = SplitConfig(),
    window_config: WindowConfig = WindowConfig(),
) -> PreparedWindows:
    """Executa partição, calibração, normalização e janelamento."""

    assigned = assign_partition(df, split_config)
    baselines = fit_motor_baselines(
        assigned,
        calibration_size=window_config.calibration_size,
        epsilon=window_config.epsilon,
    )
    normalized = normalize_by_motor(assigned, baselines)
    prepared = build_windows(normalized, window_config)
    prepared.baselines = baselines
    return prepared
