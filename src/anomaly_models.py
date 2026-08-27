"""Modelos híbridos para score de anomalia em janelas de sensores."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from src.anomaly_data import MotorBaselines, PreparedWindows, WindowConfig
from src.data_utils import FEATURES


MODEL_NAMES = ("statistical", "isolation_forest", "autoencoder")


@dataclass
class AnomalyModelBundle:
    """Modelos, transformações e thresholds necessários para inferência."""

    isolation_scaler: StandardScaler
    isolation_forest: IsolationForest
    autoencoder_scaler: StandardScaler
    autoencoder: MLPRegressor
    thresholds: dict[str, float]
    baselines: MotorBaselines | None
    window_config: WindowConfig
    summary_feature_names: list[str]
    sensor_names: list[str]
    threshold_source: str
    fit_counts: dict[str, int]
    training_info: dict[str, Any]


def statistical_scores(sequences: np.ndarray) -> np.ndarray:
    """Score auditável: maior desvio absoluto médio entre sensores."""

    if sequences.ndim != 3:
        raise ValueError("sequences deve ter shape (janelas, passos, sensores)")
    return np.max(np.mean(np.abs(sequences), axis=1), axis=1)


def _autoencoder_scores(
    sequences: np.ndarray,
    scaler: StandardScaler,
    model: MLPRegressor,
) -> tuple[np.ndarray, np.ndarray]:
    flat = sequences.reshape(len(sequences), -1)
    scaled = scaler.transform(flat)
    reconstructed = model.predict(scaled)
    absolute_error = np.abs(reconstructed - scaled)
    scores = absolute_error.mean(axis=1)
    sensor_errors = absolute_error.reshape(
        len(sequences), sequences.shape[1], sequences.shape[2]
    ).mean(axis=1)
    return scores, sensor_errors


def _score_core(
    prepared: PreparedWindows,
    isolation_scaler: StandardScaler,
    isolation_forest: IsolationForest,
    autoencoder_scaler: StandardScaler,
    autoencoder: MLPRegressor,
) -> tuple[dict[str, np.ndarray], np.ndarray]:
    isolation_input = isolation_scaler.transform(prepared.summaries)
    isolation_score = -isolation_forest.score_samples(isolation_input)
    autoencoder_score, sensor_errors = _autoencoder_scores(
        prepared.sequences, autoencoder_scaler, autoencoder
    )
    scores = {
        "statistical": statistical_scores(prepared.sequences),
        "isolation_forest": isolation_score,
        "autoencoder": autoencoder_score,
    }
    return scores, sensor_errors


def fit_anomaly_models(
    prepared: PreparedWindows,
    threshold_quantile: float = 0.99,
) -> AnomalyModelBundle:
    """Treina em normais de treino e calibra thresholds em normais de validação."""

    if not 0 < threshold_quantile < 1:
        raise ValueError("threshold_quantile deve estar entre 0 e 1")
    metadata = prepared.metadata
    train_mask = (
        metadata["partition"].eq("train") & metadata["train_eligible"].astype(bool)
    ).to_numpy()
    validation_mask = (
        metadata["partition"].eq("validation")
        & metadata["train_eligible"].astype(bool)
    ).to_numpy()
    if train_mask.sum() < 20:
        raise ValueError("São necessárias pelo menos 20 janelas normais de treino")
    if validation_mask.sum() < 10:
        raise ValueError("São necessárias pelo menos 10 janelas normais de validação")

    train_summaries = prepared.summaries[train_mask]
    isolation_scaler = StandardScaler().fit(train_summaries)
    isolation_forest = IsolationForest(
        n_estimators=300,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    ).fit(isolation_scaler.transform(train_summaries))

    train_flat = prepared.sequences[train_mask].reshape(int(train_mask.sum()), -1)
    autoencoder_scaler = StandardScaler().fit(train_flat)
    train_flat_scaled = autoencoder_scaler.transform(train_flat)
    autoencoder = MLPRegressor(
        hidden_layer_sizes=(64, 16, 64),
        activation="relu",
        solver="adam",
        early_stopping=True,
        validation_fraction=0.15,
        n_iter_no_change=15,
        max_iter=300,
        batch_size=64,
        random_state=42,
    )
    autoencoder.fit(train_flat_scaled, train_flat_scaled)

    temporary_bundle = AnomalyModelBundle(
        isolation_scaler=isolation_scaler,
        isolation_forest=isolation_forest,
        autoencoder_scaler=autoencoder_scaler,
        autoencoder=autoencoder,
        thresholds={},
        baselines=prepared.baselines,
        window_config=prepared.config,
        summary_feature_names=prepared.feature_names,
        sensor_names=list(FEATURES),
        threshold_source="validation_normal_guard_clean",
        fit_counts={
            "train": int(train_mask.sum()),
            "validation_threshold": int(validation_mask.sum()),
        },
        training_info={
            "threshold_quantile": threshold_quantile,
            "autoencoder_iterations": int(autoencoder.n_iter_),
            "autoencoder_loss": float(autoencoder.loss_),
        },
    )
    validation_windows = PreparedWindows(
        sequences=prepared.sequences[validation_mask],
        summaries=prepared.summaries[validation_mask],
        metadata=metadata.loc[validation_mask].reset_index(drop=True),
        feature_names=prepared.feature_names,
        baselines=prepared.baselines,
        config=prepared.config,
    )
    validation_scores, _ = _score_core(
        validation_windows,
        isolation_scaler,
        isolation_forest,
        autoencoder_scaler,
        autoencoder,
    )
    temporary_bundle.thresholds = {
        name: float(np.quantile(values, threshold_quantile))
        for name, values in validation_scores.items()
    }
    return temporary_bundle


def apply_threshold_and_persistence(
    scores: np.ndarray,
    threshold: float,
    motor_ids: np.ndarray,
    min_consecutive: int = 3,
) -> tuple[np.ndarray, np.ndarray]:
    """Aplica threshold e exige sequência consecutiva dentro de cada motor."""

    if min_consecutive <= 0:
        raise ValueError("min_consecutive deve ser positivo")
    scores = np.asarray(scores, dtype=float)
    motor_ids = np.asarray(motor_ids)
    if len(scores) != len(motor_ids):
        raise ValueError("scores e motor_ids devem ter o mesmo tamanho")
    alerts = scores > threshold
    persistent = np.zeros(len(alerts), dtype=bool)
    run_length = 0
    previous_motor: object | None = None
    for index, (motor_id, alert) in enumerate(zip(motor_ids, alerts, strict=True)):
        if motor_id != previous_motor:
            run_length = 0
        run_length = run_length + 1 if alert else 0
        persistent[index] = run_length >= min_consecutive
        previous_motor = motor_id
    return alerts, persistent


def score_anomaly_models(
    prepared: PreparedWindows,
    bundle: AnomalyModelBundle,
    min_consecutive: int = 3,
) -> pd.DataFrame:
    """Gera scores, alertas brutos, persistência e erros por sensor."""

    scores, sensor_errors = _score_core(
        prepared,
        bundle.isolation_scaler,
        bundle.isolation_forest,
        bundle.autoencoder_scaler,
        bundle.autoencoder,
    )
    scored = prepared.metadata.reset_index(drop=True).copy()
    motor_ids = scored["motor_id"].to_numpy()
    for model_name, values in scores.items():
        threshold = bundle.thresholds[model_name]
        alerts, persistent = apply_threshold_and_persistence(
            values, threshold, motor_ids, min_consecutive=min_consecutive
        )
        scored[f"{model_name}_score"] = values
        scored[f"{model_name}_threshold"] = threshold
        scored[f"{model_name}_alert"] = alerts
        scored[f"{model_name}_persistent"] = persistent
    for sensor_index, sensor_name in enumerate(bundle.sensor_names):
        scored[f"ae_error_{sensor_name}"] = sensor_errors[:, sensor_index]
    return scored
