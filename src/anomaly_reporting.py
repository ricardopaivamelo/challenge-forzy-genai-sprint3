"""Geração de figuras e relatório acadêmico da Sprint 3."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.data_utils import FEATURES, TIPOS_FALHA


SENSOR_LABELS = {
    "rotacao_rpm": "Rotação (rpm)",
    "vibracao_mm_s": "Vibração (mm/s)",
    "temperatura_c": "Temperatura (°C)",
    "corrente_a": "Corrente (A)",
}
MODEL_LABELS = {
    "statistical": "Baseline estatístico",
    "isolation_forest": "Isolation Forest",
    "autoencoder": "Autoencoder",
    "sprint2": "Random Forest — Sprint 2",
}


def _save(fig: plt.Figure, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def generate_figures(
    readings: pd.DataFrame,
    scored: pd.DataFrame,
    motor_ranking: pd.DataFrame,
    sensor_ranking: pd.DataFrame,
    metrics: dict[str, object],
    output_dir: Path,
) -> list[Path]:
    """Exporta sete visualizações estáticas exigidas pela rubrica."""

    output_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")
    paths: list[Path] = []

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    status = np.where(readings["falha"].eq(0), "Normal", "Falha rotulada")
    for axis, feature in zip(axes.flat, FEATURES, strict=True):
        for label, color in (("Normal", "#2a9d8f"), ("Falha rotulada", "#e76f51")):
            values = readings.loc[status == label, feature]
            axis.hist(values, bins=35, density=True, alpha=0.55, label=label, color=color)
        axis.set_title(SENSOR_LABELS[feature])
        axis.set_ylabel("Densidade")
    axes[0, 0].legend()
    fig.suptitle("Distribuição histórica dos sensores por estado", y=1.01)
    paths.append(_save(fig, output_dir / "s3_01_distribuicao_sensores.png"))

    focus_motor = int(motor_ranking.iloc[0]["motor_id"])
    motor_readings = readings.loc[readings["motor_id"].eq(focus_motor)].sort_values("timestamp")
    fig, axes = plt.subplots(4, 1, figsize=(13, 10), sharex=True)
    fault_mask = motor_readings["falha"].gt(0)
    for axis, feature in zip(axes, FEATURES, strict=True):
        axis.plot(motor_readings["timestamp"], motor_readings[feature], linewidth=1, color="#264653")
        axis.scatter(
            motor_readings.loc[fault_mask, "timestamp"],
            motor_readings.loc[fault_mask, feature],
            s=8,
            color="#e63946",
            label="Falha rotulada",
        )
        axis.set_ylabel(SENSOR_LABELS[feature])
    axes[0].legend(loc="upper right")
    axes[-1].set_xlabel("Tempo")
    fig.suptitle(f"Evolução temporal — motor {focus_motor}")
    paths.append(_save(fig, output_dir / "s3_02_evolucao_temporal.png"))

    fig, axis = plt.subplots(figsize=(8, 6))
    correlation = readings[FEATURES].corr()
    sns.heatmap(correlation, annot=True, fmt=".2f", cmap="vlag", center=0, ax=axis)
    axis.set_xticklabels([SENSOR_LABELS[name] for name in FEATURES], rotation=30, ha="right")
    axis.set_yticklabels([SENSOR_LABELS[name] for name in FEATURES], rotation=0)
    axis.set_title("Correlação entre sensores")
    paths.append(_save(fig, output_dir / "s3_03_correlacao.png"))

    motor_scores = scored.loc[
        scored["partition"].eq("test") & scored["motor_id"].eq(focus_motor)
    ].sort_values("timestamp")
    fig, axis = plt.subplots(figsize=(13, 5))
    for model_name, color in (
        ("statistical", "#2a9d8f"),
        ("isolation_forest", "#e9c46a"),
        ("autoencoder", "#e76f51"),
    ):
        ratio = motor_scores[f"{model_name}_score"] / motor_scores[f"{model_name}_threshold"]
        axis.plot(motor_scores["timestamp"], ratio, label=MODEL_LABELS[model_name], linewidth=1.2, color=color)
    axis.axhline(1.0, color="black", linestyle="--", linewidth=1, label="Threshold")
    anomalous = motor_scores["y_anomaly"].eq(1)
    axis.fill_between(
        motor_scores["timestamp"], 0, 1,
        where=anomalous,
        transform=axis.get_xaxis_transform(),
        color="#e63946", alpha=0.10, label="Falha rotulada",
    )
    axis.set_ylabel("Score / threshold")
    axis.set_xlabel("Tempo")
    axis.set_title(f"Scores de anomalia ao longo do tempo — motor {focus_motor}")
    axis.legend(ncol=3, fontsize=8)
    paths.append(_save(fig, output_dir / "s3_04_scores_tempo.png"))

    fig, axes = plt.subplots(2, 2, figsize=(10, 9))
    for axis, model_name in zip(
        axes.flat,
        ("statistical", "isolation_forest", "autoencoder", "sprint2"),
        strict=True,
    ):
        cm = np.asarray(metrics["window_metrics"][model_name]["confusion_matrix"])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=axis)
        axis.set_title(MODEL_LABELS[model_name])
        axis.set_xlabel("Predito")
        axis.set_ylabel("Real")
        axis.set_xticklabels(["Normal", "Anomalia"])
        axis.set_yticklabels(["Normal", "Anomalia"], rotation=0)
    fig.suptitle("Matrizes de confusão nas janelas de teste", y=1.01)
    paths.append(_save(fig, output_dir / "s3_05_matrizes_confusao.png"))

    fig, axis = plt.subplots(figsize=(10, 5))
    ranking_plot = motor_ranking.sort_values("persistent_rate", ascending=True)
    axis.barh(ranking_plot["motor_id"].astype(str), ranking_plot["alert_rate"], label="Alertas", color="#e9c46a")
    axis.barh(ranking_plot["motor_id"].astype(str), ranking_plot["persistent_rate"], label="Persistentes", color="#e76f51")
    axis.set_xlabel("Proporção de janelas")
    axis.set_ylabel("Motor")
    axis.set_title("Ranking de motores por alertas do Autoencoder")
    axis.legend()
    paths.append(_save(fig, output_dir / "s3_06_ranking_motores.png"))

    fig, axis = plt.subplots(figsize=(9, 5))
    axis.bar(
        [SENSOR_LABELS.get(sensor, sensor) for sensor in sensor_ranking["sensor"]],
        sensor_ranking["mean_error"],
        color="#457b9d",
    )
    for index, row in sensor_ranking.reset_index(drop=True).iterrows():
        axis.text(index, row["mean_error"], str(int(row["dominant_alert_count"])), ha="center", va="bottom")
    axis.set_ylabel("Erro médio de reconstrução")
    axis.set_title("Sensores nos alertas do Autoencoder\n(número = alertas em que o sensor foi dominante)")
    axis.tick_params(axis="x", rotation=20)
    paths.append(_save(fig, output_dir / "s3_07_contribuicao_sensores.png"))
    return paths


def render_report(
    metrics: dict[str, object],
    motor_ranking: pd.DataFrame,
    sensor_ranking: pd.DataFrame,
) -> str:
    """Produz relatório completo usando somente números calculados pelo pipeline."""

    window = metrics["window_metrics"]
    events = metrics["event_metrics"]
    data = metrics["data"]
    thresholds = metrics["thresholds"]
    rows = []
    for model_name in ("statistical", "isolation_forest", "autoencoder", "sprint2"):
        item = window[model_name]
        rows.append(
            f"| {MODEL_LABELS[model_name]} | {item['precision']:.3f} | {item['recall']:.3f} | "
            f"{item['f1']:.3f} | {item['pr_auc']:.3f} | {item['roc_auc']:.3f} | "
            f"{item['false_positive_rate']:.3f} |"
        )
    event_rows = []
    for model_name in ("statistical", "isolation_forest", "autoencoder", "sprint2"):
        item = events[model_name]
        lead = "—" if item["median_lead_minutes"] is None else f"{item['median_lead_minutes']:.1f}"
        event_rows.append(
            f"| {MODEL_LABELS[model_name]} | {item['detected_events']}/{item['events']} | "
            f"{item['event_recall']:.3f} | {item['anticipated_events']} | {lead} |"
        )
    top_motor = motor_ranking.iloc[0]
    top_sensor = sensor_ranking.iloc[0]
    return f"""# Relatório técnico — Sprint 3: Baseline e Detecção de Anomalias

## 1. Descrição do problema de anomalias

O objetivo é aprender o comportamento normal de cada motor e sinalizar desvios em janelas de
30 minutos. A abordagem é **semissupervisionada**: rótulos curam treino/validação e avaliam o
resultado, mas não são alvo do Isolation Forest nem do Autoencoder. Alerta indica prioridade
de inspeção, não causa comprovada.

## 2. Descrição dos dados da Forzy

O SQLite contém **{data['readings']:,} leituras**, **{data['motors']} motores**, período de
{data['start']} a {data['end']} e frequência de um minuto. Os sensores são rotação, vibração,
temperatura e corrente; `falha` identifica normalidade (0) ou três classes conhecidas (1–3).
Os dados são sintéticos e não validam desempenho industrial real.

## 3. Análise exploratória

As figuras `s3_01` a `s3_03` mostram distribuições, evolução temporal e correlações. As falhas
são progressivas e os níveis normais variam entre motores, justificando baseline individual.
A base não possui valores ausentes nem timestamps duplicados na análise executada.

## 4. Baseline operacional

Cada motor usa mediana e IQR das primeiras 30 leituras. Janelas têm 30 minutos e stride de
cinco minutos. O baseline estatístico usa o maior desvio absoluto médio entre sensores; os
thresholds de percentil 99 da validação são: estatístico **{thresholds['statistical']:.4f}**,
Isolation Forest **{thresholds['isolation_forest']:.4f}** e Autoencoder
**{thresholds['autoencoder']:.4f}**.

## 5. Preparação dos dados

Treino, validação e teste são separados por motor. O teste preserva `[1, 2, 10, 15, 16]`.
Janelas de treino precisam ser totalmente normais e ficar 30 minutos afastadas de falhas.
Normalização usa somente o período inicial do próprio motor; janelas com lacunas são descartadas.

## 6. Treinamento dos modelos

Foram treinados Isolation Forest com 300 árvores e Autoencoder denso 120–64–16–64–120.
O Autoencoder aprendeu `X → X`; MAE de reconstrução é o score e o erro agregado por sensor
apoia a explicação. O baseline estatístico funciona como referência auditável.

## 7. Avaliação dos resultados

| Modelo | Precision | Recall | F1 | PR-AUC | ROC-AUC | FPR |
|---|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

| Modelo | Eventos detectados | Recall por evento | Antecipados | Lead mediano (min) |
|---|---:|---:|---:|---:|
{chr(10).join(event_rows)}

O melhor PR-AUC entre os detectores de anomalia foi **{metrics['best_anomaly_model']}**. O
resultado mostra que complexidade não garante superioridade: o baseline estatístico é uma
referência forte nesta base sintética.

## 8. Análise dos casos anômalos

O motor mais destacado pelo Autoencoder foi o **{int(top_motor['motor_id'])}**, com taxa de
alerta de **{top_motor['alert_rate']:.1%}** e persistência de
**{top_motor['persistent_rate']:.1%}**. O maior erro médio nos alertas ocorreu em
**{SENSOR_LABELS.get(top_sensor['sensor'], top_sensor['sensor'])}**. Esses erros são
associações do modelo, não atribuição causal da falha.

## 9. Comparação com a Sprint 2

O Random Forest supervisionado reconhece classes conhecidas e obteve F1 binário de
**{window['sprint2']['f1']:.3f}** nos mesmos endpoints. Os detectores encontram desvios sem
receber a classe de falha e podem alertar antes do rótulo. As abordagens são complementares:
anomalia prioriza investigação; classificação sugere uma categoria conhecida.

## 10. Visualização dos resultados

Sete PNGs mostram sensores, tempo, correlação, scores/thresholds, matrizes de confusão,
ranking de motores e erros por sensor. Os CSVs preservam todos os scores para auditoria.

## 11. Integração futura com agente conversacional

`build_agent_payload()` retorna motor, timestamp, score, threshold, severidade, persistência,
sensores dominantes e explicação. Um LLM futuro poderá reformular esses fatos, mas a decisão e
os números permanecem no pipeline determinístico.

## 12. Código e organização

O comando `python src/run_sprint3.py` recria modelo, métricas, scores, ranking, relatório e
figuras. Testes automatizados cobrem partição, calibração, janelas, thresholds, persistência,
eventos, comparação e contrato conversacional. O notebook executado apresenta todo o fluxo.

## Limitações

- dados sintéticos e apenas 25 horas por motor;
- primeiras 30 leituras assumidas como período de comissionamento saudável;
- threshold calibrado nesta base pode não transferir para produção;
- rótulo atrasado dificulta distinguir antecipação real de falso positivo pré-evento;
- erro por sensor explica reconstrução, não causa física.
"""

