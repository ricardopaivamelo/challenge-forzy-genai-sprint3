from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import joblib
import numpy as np
import pandas as pd

from src.run_sprint3 import run_pipeline


ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_generates_finite_metrics_and_reproducible_artifacts(tmp_path):
    result = run_pipeline(
        max_motors=6,
        save_artifacts=True,
        output_root=tmp_path,
    )

    assert set(result.bundle.thresholds) == {
        "statistical",
        "isolation_forest",
        "autoencoder",
    }
    assert np.isfinite(list(result.bundle.thresholds.values())).all()
    assert not result.scored.empty
    for model_metrics in result.metrics["window_metrics"].values():
        for metric in ("precision", "recall", "f1", "false_positive_rate"):
            assert 0 <= model_metrics[metric] <= 1

    metrics_path = tmp_path / "models" / "anomaly_metrics.json"
    model_path = tmp_path / "models" / "modelo_anomalias.joblib"
    score_path = tmp_path / "results" / "anomaly_scores.csv"
    acceleration_path = tmp_path / "results" / "acceleration_contract_metrics.json"
    assert metrics_path.exists()
    assert model_path.exists()
    assert score_path.exists()
    assert acceleration_path.exists()
    assert len(list((tmp_path / "figuras").glob("s3_*.png"))) == 7
    assert json.loads(metrics_path.read_text(encoding="utf-8"))["data"]["motors"] == 6
    acceleration = json.loads(acceleration_path.read_text(encoding="utf-8"))
    assert acceleration["normal_readings"] > 0
    assert acceleration["attention_min"] < acceleration["critical_min"]
    assert joblib.load(model_path).threshold_source == "validation_normal_guard_clean"
    assert len(pd.read_csv(score_path)) == len(result.scored)


def test_documented_script_command_runs_from_repository_root(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "src/run_sprint3.py",
            "--max-motors",
            "6",
            "--output-root",
            str(tmp_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Sprint 3 concluída" in completed.stdout
