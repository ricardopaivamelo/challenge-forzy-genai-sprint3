"""Treino do modelo baseline de classificação de falhas — Sprint 2 GenAI (Forzy).

- Features: 4 leituras instantâneas (mesma assinatura da tool do agente).
- Split: StratifiedGroupKFold por motor_id (sem vazamento de nível basal entre
  treino/teste; estratificado para garantir as classes raras no teste).
- Modelo: RandomForest com class_weight balanceado (lida com o desbalanceamento e
  expõe feature_importances para o agente explicar o diagnóstico).
"""
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import classification_report, confusion_matrix, f1_score

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_utils import load_leituras, FEATURES, TARGET, TIPOS_FALHA

HERE = Path(__file__).resolve().parent
SPRINT = HERE.parent
MODELS = SPRINT / "models"
LABELS = [0, 1, 2, 3]
TARGET_NAMES = [TIPOS_FALHA[c] for c in LABELS]


def make_split(df: pd.DataFrame, n_splits: int = 4, seed: int = 42):
    """Primeiro fold de um StratifiedGroupKFold por motor_id -> (idx_treino, idx_teste)."""
    sgkf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return next(sgkf.split(df[FEATURES], df[TARGET], groups=df["motor_id"]))


def train(df: pd.DataFrame | None = None, save: bool = True) -> dict:
    if df is None:
        df = load_leituras()

    tr_idx, te_idx = make_split(df)
    Xtr, ytr = df.iloc[tr_idx][FEATURES], df.iloc[tr_idx][TARGET]
    Xte, yte = df.iloc[te_idx][FEATURES], df.iloc[te_idx][TARGET]
    motores_te = sorted(df.iloc[te_idx]["motor_id"].unique().tolist())
    motores_tr = sorted(df.iloc[tr_idx]["motor_id"].unique().tolist())

    clf = RandomForestClassifier(
        n_estimators=300, class_weight="balanced_subsample",
        random_state=42, n_jobs=-1,
    )
    clf.fit(Xtr, ytr)

    ypred = clf.predict(Xte)
    report = classification_report(
        yte, ypred, labels=LABELS, target_names=TARGET_NAMES,
        output_dict=True, zero_division=0,
    )
    cm = confusion_matrix(yte, ypred, labels=LABELS)
    macro_f1 = f1_score(yte, ypred, labels=LABELS, average="macro", zero_division=0)
    importances = dict(zip(FEATURES, clf.feature_importances_.round(4).tolist()))

    if save:
        MODELS.mkdir(exist_ok=True)
        joblib.dump(
            {"model": clf, "features": FEATURES, "labels": LABELS,
             "tipos_falha": TIPOS_FALHA, "feature_importances": importances},
            MODELS / "modelo_falhas.joblib", compress=3,
        )
        (MODELS / "metrics.json").write_text(json.dumps({
            "macro_f1": macro_f1,
            "accuracy": report["accuracy"],
            "por_classe": {TIPOS_FALHA[c]: report[TIPOS_FALHA[c]] for c in LABELS},
            "confusion_matrix": cm.tolist(),
            "feature_importances": importances,
            "motores_treino": motores_tr, "motores_teste": motores_te,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"report": report, "cm": cm, "macro_f1": macro_f1,
            "importances": importances, "motores_te": motores_te,
            "yte": yte.values, "ypred": ypred, "clf": clf, "df": df,
            "te_idx": te_idx}


if __name__ == "__main__":
    r = train()
    print(f"motores teste: {r['motores_te']}")
    print(f"\nmacro-F1: {r['macro_f1']:.3f} | accuracy: {r['report']['accuracy']:.3f}\n")
    print(f"{'classe':18s} {'precision':>9s} {'recall':>8s} {'f1':>7s} {'support':>8s}")
    for c in LABELS:
        m = r["report"][TIPOS_FALHA[c]]
        print(f"{TIPOS_FALHA[c]:18s} {m['precision']:9.3f} {m['recall']:8.3f} "
              f"{m['f1-score']:7.3f} {int(m['support']):8d}")
    print("\nmatriz de confusão (linhas=real, colunas=previsto), labels 0..3:")
    print(r["cm"])
    print("\nimportância das features:", r["importances"])
