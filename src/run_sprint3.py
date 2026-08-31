"""Orquestra todos os artefatos reproduzíveis da Sprint 3."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd

from src.anomaly_data import PreparedWindows, prepare_windows
from src.anomaly_evaluation import (
    binary_metrics,
    build_motor_ranking,
    build_sensor_ranking,
    compare_sprint2,
    evaluate_events,
    extract_fault_events,
)
from src.anomaly_models import (
    AnomalyModelBundle,
    MODEL_NAMES,
    fit_anomaly_models,
    score_anomaly_models,
)
from src.anomaly_reporting import generate_figures, render_report
from src.acceleration import calibrate_acceleration_thresholds, simulate_acceleration
from src.data_utils import load_leituras


ROOT = PROJECT_ROOT


@dataclass
class PipelineResult:
    bundle: AnomalyModelBundle
    prepared: PreparedWindows
    scored: pd.DataFrame
    metrics: dict[str, object]
    motor_ranking: pd.DataFrame
    sensor_ranking: pd.DataFrame
    event_details: pd.DataFrame


def _json_default(value: object) -> object:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    raise TypeError(f"Tipo não serializável: {type(value).__name__}")


def _data_summary(readings: pd.DataFrame, prepared: PreparedWindows) -> dict[str, object]:
    return {
        "motors": int(readings["motor_id"].nunique()),
        "readings": int(len(readings)),
        "windows": int(len(prepared.metadata)),
        "start": pd.Timestamp(readings["timestamp"].min()).isoformat(),
        "end": pd.Timestamp(readings["timestamp"].max()).isoformat(),
        "missing_values": int(readings.isna().sum().sum()),
        "duplicate_motor_timestamps": int(
            readings.duplicated(["motor_id", "timestamp"]).sum()
        ),
        "label_counts": {
            str(int(label)): int(count)
            for label, count in readings["falha"].value_counts().sort_index().items()
        },
        "partition_windows": {
            str(name): int(count)
            for name, count in prepared.metadata["partition"].value_counts().items()
        },
    }


def run_pipeline(
    *,
    max_motors: int | None = None,
    save_artifacts: bool = True,
    output_root: Path | str = ROOT,
) -> PipelineResult:
    """Treina, avalia e opcionalmente persiste todos os entregáveis."""

    output_root = Path(output_root)
    readings = load_leituras(join_motores=False)
    if max_motors is not None:
        if max_motors < 6:
            raise ValueError("max_motors deve ser pelo menos 6 para conter treino/validação/teste")
        selected = sorted(readings["motor_id"].unique())[:max_motors]
        readings = readings.loc[readings["motor_id"].isin(selected)].copy()

    readings = simulate_acceleration(readings, seed=42)
    acceleration_contract = calibrate_acceleration_thresholds(readings)

    prepared = prepare_windows(readings)
    bundle = fit_anomaly_models(prepared)
    scored = score_anomaly_models(prepared, bundle)
    scored = compare_sprint2(readings, scored, ROOT / "models" / "modelo_falhas.joblib")
    test = scored.loc[scored["partition"].eq("test")].copy()
    if test.empty:
        raise ValueError("Partição de teste vazia")

    window_metrics: dict[str, dict[str, object]] = {}
    for model_name in MODEL_NAMES:
        window_metrics[model_name] = binary_metrics(
            test["y_anomaly"].to_numpy(),
            test[f"{model_name}_score"].to_numpy(),
            bundle.thresholds[model_name],
        )
    window_metrics["sprint2"] = binary_metrics(
        test["y_anomaly"].to_numpy(),
        test["sprint2_score"].to_numpy(),
        threshold=0.5,
        predictions=test["sprint2_alert"].to_numpy(),
    )

    test_motors = sorted(test["motor_id"].unique())
    events = extract_fault_events(readings.loc[readings["motor_id"].isin(test_motors)])
    event_frames: list[pd.DataFrame] = []
    event_metrics: dict[str, dict[str, object]] = {}
    for model_name in (*MODEL_NAMES, "sprint2"):
        details, summary = evaluate_events(events, test, model_name)
        details.insert(0, "model", model_name)
        event_frames.append(details)
        event_metrics[model_name] = summary
    event_details = pd.concat(event_frames, ignore_index=True)

    motor_ranking = build_motor_ranking(scored, "autoencoder", partition="test")
    sensor_ranking = build_sensor_ranking(scored, partition="test")
    best_anomaly_model = max(
        MODEL_NAMES,
        key=lambda name: float(window_metrics[name]["pr_auc"] or 0.0),
    )
    metrics: dict[str, object] = {
        "data": _data_summary(readings, prepared),
        "split": {
            "train_motors": sorted(
                int(value)
                for value in prepared.metadata.query("partition == 'train'")["motor_id"].unique()
            ),
            "validation_motors": sorted(
                int(value)
                for value in prepared.metadata.query("partition == 'validation'")["motor_id"].unique()
            ),
            "test_motors": [int(value) for value in test_motors],
        },
        "window_config": {
            "window_size": prepared.config.window_size,
            "stride": prepared.config.stride,
            "calibration_size": prepared.config.calibration_size,
            "guard_size": prepared.config.guard_size,
        },
        "thresholds": bundle.thresholds,
        "threshold_source": bundle.threshold_source,
        "fit_counts": bundle.fit_counts,
        "training_info": bundle.training_info,
        "window_metrics": window_metrics,
        "event_metrics": event_metrics,
        "best_anomaly_model": best_anomaly_model,
        "acceleration_contract": acceleration_contract,
    }

    if save_artifacts:
        models_dir = output_root / "models"
        results_dir = output_root / "results"
        figures_dir = output_root / "figuras"
        docs_dir = output_root / "docs"
        for directory in (models_dir, results_dir, figures_dir, docs_dir):
            directory.mkdir(parents=True, exist_ok=True)
        joblib.dump(bundle, models_dir / "modelo_anomalias.joblib", compress=3)
        (models_dir / "anomaly_metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )
        scored.to_csv(results_dir / "anomaly_scores.csv", index=False)
        motor_ranking.to_csv(results_dir / "motor_ranking.csv", index=False)
        sensor_ranking.to_csv(results_dir / "sensor_ranking.csv", index=False)
        event_details.to_csv(results_dir / "event_detections.csv", index=False)
        (results_dir / "acceleration_contract_metrics.json").write_text(
            json.dumps(
                acceleration_contract,
                ensure_ascii=False,
                indent=2,
                default=_json_default,
            ),
            encoding="utf-8",
        )
        generate_figures(
            readings, scored, motor_ranking, sensor_ranking, metrics, figures_dir
        )
        (docs_dir / "sprint3_report.md").write_text(
            render_report(metrics, motor_ranking, sensor_ranking), encoding="utf-8"
        )

    return PipelineResult(
        bundle=bundle,
        prepared=prepared,
        scored=scored,
        metrics=metrics,
        motor_ranking=motor_ranking,
        sensor_ranking=sensor_ranking,
        event_details=event_details,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-motors", type=int, default=None)
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = run_pipeline(max_motors=args.max_motors, output_root=args.output_root)
    print("Sprint 3 concluída")
    print("Thresholds:", {name: round(value, 4) for name, value in result.bundle.thresholds.items()})
    print("Melhor detector por PR-AUC:", result.metrics["best_anomaly_model"])
    for name, values in result.metrics["window_metrics"].items():
        print(f"{name:18s} F1={values['f1']:.3f} PR-AUC={values['pr_auc']:.3f}")
