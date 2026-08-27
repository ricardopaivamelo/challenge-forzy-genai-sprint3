"""Métricas de janela, eventos e comparação com o classificador da Sprint 2."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    auc,
    confusion_matrix,
    precision_recall_curve,
    precision_recall_fscore_support,
    roc_auc_score,
)

from src.data_utils import FEATURES


def binary_metrics(
    y_true: np.ndarray,
    scores: np.ndarray,
    threshold: float,
    predictions: np.ndarray | None = None,
) -> dict[str, object]:
    """Calcula métricas binárias com orientação 1 = anomalia."""

    y_true = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)
    y_pred = (
        np.asarray(predictions, dtype=bool)
        if predictions is not None
        else scores > threshold
    )
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    false_positive_rate = fp / (fp + tn) if fp + tn else 0.0
    if len(np.unique(y_true)) == 2:
        roc_auc = float(roc_auc_score(y_true, scores))
        pr_precision, pr_recall, _ = precision_recall_curve(y_true, scores)
        pr_auc = float(auc(pr_recall, pr_precision))
    else:
        roc_auc = None
        pr_auc = None
    return {
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "false_positive_rate": float(false_positive_rate),
        "support_normal": int((y_true == 0).sum()),
        "support_anomaly": int((y_true == 1).sum()),
        "confusion_matrix": cm.astype(int).tolist(),
        "true_positive": int(tp),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_negative": int(tn),
    }


def extract_fault_events(readings: pd.DataFrame) -> pd.DataFrame:
    """Agrupa qualquer sequência positiva contígua em um episódio de falha."""

    required = {"motor_id", "timestamp", "falha"}
    missing = required - set(readings.columns)
    if missing:
        raise ValueError(f"Colunas ausentes para eventos: {sorted(missing)}")
    ordered = readings.sort_values(["motor_id", "timestamp"])
    positive = ordered.loc[ordered["falha"].gt(0), ["motor_id", "timestamp", "falha"]].copy()
    columns = [
        "event_id",
        "motor_id",
        "fault_classes",
        "primary_fault_class",
        "start",
        "end",
        "duration_minutes",
        "previous_end",
    ]
    if positive.empty:
        return pd.DataFrame(columns=columns)
    previous_motor = positive["motor_id"].shift()
    previous_timestamp = positive["timestamp"].shift()
    new_event = positive["motor_id"].ne(previous_motor) | (
        positive["timestamp"] - previous_timestamp
    ).ne(pd.Timedelta(minutes=1))
    positive["event_group"] = new_event.cumsum()

    events: list[dict[str, object]] = []
    for event_id, (_, group) in enumerate(positive.groupby("event_group", sort=True), start=1):
        counts = group["falha"].value_counts()
        most_common = counts.loc[counts.eq(counts.max())].index.min()
        classes_in_order = list(dict.fromkeys(int(value) for value in group["falha"]))
        events.append(
            {
                "event_id": event_id,
                "motor_id": int(group["motor_id"].iloc[0]),
                "fault_classes": ",".join(str(value) for value in classes_in_order),
                "primary_fault_class": int(most_common),
                "start": pd.Timestamp(group["timestamp"].iloc[0]),
                "end": pd.Timestamp(group["timestamp"].iloc[-1]),
            }
        )
    result = pd.DataFrame(events)
    result["duration_minutes"] = (
        (result["end"] - result["start"]).dt.total_seconds() / 60 + 1
    ).astype(int)
    result["previous_end"] = result.groupby("motor_id")["end"].shift()
    return result[columns]


def evaluate_events(
    events: pd.DataFrame,
    scored: pd.DataFrame,
    model_name: str,
    lead_window_minutes: int = 60,
    window_size_minutes: int = 30,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Mede detecção persistente e antecedência por evento rotulado."""

    persistent_column = f"{model_name}_persistent"
    if persistent_column not in scored:
        raise ValueError(f"Coluna ausente: {persistent_column}")
    details: list[dict[str, object]] = []
    for event in events.itertuples(index=False):
        window_start = pd.Timestamp(event.start) - pd.Timedelta(
            minutes=lead_window_minutes
        )
        previous_end = getattr(event, "previous_end", pd.NaT)
        if not pd.isna(previous_end):
            clean_start = pd.Timestamp(previous_end) + pd.Timedelta(
                minutes=window_size_minutes
            )
            window_start = max(window_start, clean_start)
        before_event = scored["timestamp"].ge(window_start) & scored["timestamp"].lt(
            event.start
        )
        during_event = scored["timestamp"].between(event.start, event.end)
        candidates = scored.loc[
            scored["motor_id"].eq(event.motor_id)
            & (before_event | during_event)
            & scored[persistent_column].astype(bool)
        ].sort_values("timestamp")
        detected = not candidates.empty
        first_alert = candidates.iloc[0]["timestamp"] if detected else pd.NaT
        lead_minutes = (
            (pd.Timestamp(event.start) - pd.Timestamp(first_alert)).total_seconds() / 60
            if detected
            else np.nan
        )
        details.append(
            {
                **event._asdict(),
                "detected": detected,
                "first_alert": first_alert,
                "lead_minutes": lead_minutes,
                "anticipated": bool(detected and lead_minutes > 0),
            }
        )
    detail_frame = pd.DataFrame(details)
    detected_frame = (
        detail_frame.loc[detail_frame["detected"]] if not detail_frame.empty else detail_frame
    )
    summary = {
        "events": int(len(detail_frame)),
        "detected_events": int(detail_frame["detected"].sum())
        if not detail_frame.empty
        else 0,
        "event_recall": float(detail_frame["detected"].mean())
        if not detail_frame.empty
        else 0.0,
        "anticipated_events": int(detail_frame["anticipated"].sum())
        if not detail_frame.empty
        else 0,
        "median_lead_minutes": float(detected_frame["lead_minutes"].median())
        if not detected_frame.empty
        else None,
    }
    return detail_frame, summary


def _persistent_flags(
    alerts: np.ndarray, motor_ids: np.ndarray, min_consecutive: int = 3
) -> np.ndarray:
    persistent = np.zeros(len(alerts), dtype=bool)
    previous_motor: object | None = None
    run_length = 0
    for index, (motor_id, alert) in enumerate(
        zip(motor_ids, alerts, strict=True)
    ):
        if motor_id != previous_motor:
            run_length = 0
        run_length = run_length + 1 if alert else 0
        persistent[index] = run_length >= min_consecutive
        previous_motor = motor_id
    return persistent


def compare_sprint2(
    readings: pd.DataFrame,
    scored: pd.DataFrame,
    model_path: Path | str,
    min_consecutive: int = 3,
) -> pd.DataFrame:
    """Aplica o Random Forest antigo exatamente nos endpoints das janelas."""

    model_bundle = joblib.load(Path(model_path))
    classifier = model_bundle["model"]
    features = model_bundle.get("features", FEATURES)
    endpoints = readings[["motor_id", "timestamp", *features]].copy()
    compared = scored.merge(
        endpoints,
        on=["motor_id", "timestamp"],
        how="left",
        validate="one_to_one",
    )
    if compared[features].isna().any().any():
        raise ValueError("Nem todos os endpoints foram encontrados nas leituras originais")
    probabilities = classifier.predict_proba(compared[features])
    normal_positions = np.flatnonzero(classifier.classes_ == 0)
    if len(normal_positions) != 1:
        raise ValueError("O classificador da Sprint 2 não possui classe normal 0")
    compared["sprint2_score"] = 1.0 - probabilities[:, normal_positions[0]]
    compared["sprint2_alert"] = classifier.predict(compared[features]) > 0
    compared["sprint2_persistent"] = _persistent_flags(
        compared["sprint2_alert"].to_numpy(dtype=bool),
        compared["motor_id"].to_numpy(),
        min_consecutive=min_consecutive,
    )
    return compared.drop(columns=features)


def build_motor_ranking(
    scored: pd.DataFrame,
    model_name: str = "autoencoder",
    partition: str = "test",
) -> pd.DataFrame:
    """Resume intensidade e frequência de alertas por motor."""

    subset = scored.loc[scored["partition"].eq(partition)]
    ranking = (
        subset.groupby("motor_id")
        .agg(
            windows=("y_anomaly", "size"),
            labeled_anomaly_rate=("y_anomaly", "mean"),
            alert_rate=(f"{model_name}_alert", "mean"),
            persistent_rate=(f"{model_name}_persistent", "mean"),
            mean_score=(f"{model_name}_score", "mean"),
            max_score=(f"{model_name}_score", "max"),
        )
        .reset_index()
        .sort_values(["persistent_rate", "max_score"], ascending=False)
        .reset_index(drop=True)
    )
    return ranking


def build_sensor_ranking(
    scored: pd.DataFrame,
    partition: str = "test",
) -> pd.DataFrame:
    """Resume erros do Autoencoder sem afirmar contribuição causal."""

    error_columns = [column for column in scored if column.startswith("ae_error_")]
    if not error_columns:
        raise ValueError("Scores não contêm erros do Autoencoder por sensor")
    alerted = scored.loc[
        scored["partition"].eq(partition) & scored["autoencoder_alert"].astype(bool)
    ]
    if alerted.empty:
        return pd.DataFrame(
            {
                "sensor": [column.removeprefix("ae_error_") for column in error_columns],
                "mean_error": 0.0,
                "dominant_alert_count": 0,
            }
        )
    dominant = alerted[error_columns].idxmax(axis=1)
    counts = dominant.value_counts()
    ranking = pd.DataFrame(
        {
            "sensor": [column.removeprefix("ae_error_") for column in error_columns],
            "mean_error": [float(alerted[column].mean()) for column in error_columns],
            "dominant_alert_count": [int(counts.get(column, 0)) for column in error_columns],
        }
    )
    return ranking.sort_values(
        ["mean_error", "dominant_alert_count"], ascending=False
    ).reset_index(drop=True)
