"""Gera o notebook acadêmico da Sprint 3 a partir do pipeline testado."""

from __future__ import annotations

from pathlib import Path
import sys
from textwrap import dedent

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import nbformat as nbf

from src.academic_info import academic_markdown


ROOT = PROJECT_ROOT
DEFAULT_OUTPUT = ROOT / "notebooks" / "sprint3_anomalias.ipynb"


def build_notebook() -> nbf.NotebookNode:
    """Monta narrativa e células executáveis cobrindo os 12 entregáveis."""

    cells: list[nbf.NotebookNode] = []
    md = lambda text: cells.append(nbf.v4.new_markdown_cell(dedent(text).strip()))
    code = lambda text: cells.append(nbf.v4.new_code_cell(dedent(text).strip()))

    md(
        """
        # Sprint 3 — Modelo para Baseline e Detecção de Anomalias

        **Challenge Forzy · FIAP · Manutenção preditiva de motores elétricos**
        """
    )
    md(academic_markdown())
    md(
        """
        Este notebook executa o pipeline completo, documenta as decisões metodológicas e
        apresenta os resultados usados na entrega. Todos os números são recalculados a partir
        de `data/motor.db`; nenhum serviço externo é necessário.
        """
    )
    code(
        """
        from pathlib import Path
        import sys
        import pandas as pd
        from IPython.display import Image, display

        ROOT = Path.cwd()
        if ROOT.name == "notebooks":
            ROOT = ROOT.parent
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))

        from src.run_sprint3 import run_pipeline
        from src.anomaly_service import build_agent_payload
        from src.data_utils import FEATURES, TIPOS_FALHA

        result = run_pipeline(save_artifacts=False)
        metrics = result.metrics
        scored = result.scored
        print(f"Pipeline executado: {len(scored):,} janelas; melhor detector por PR-AUC = {metrics['best_anomaly_model']}")
        """
    )

    md(
        """
        ## 1. Descrição do problema de anomalias

        Consideramos **normal** uma janela compatível com o baseline do próprio motor e
        **anômala** uma janela cujo score supera o threshold calibrado na validação.
        A abordagem é **semissupervisionada**: os rótulos selecionam períodos confiáveis e
        avaliam resultados, mas os detectores aprendem apenas o padrão normal. Isso é relevante
        porque o banco só rotula a falha depois que a degradação já ganhou intensidade.
        """
    )
    code(
        """
        pd.DataFrame({
            "Definição": ["Janela", "Alerta", "Persistência", "Antecipação"],
            "Regra": ["30 leituras / 30 minutos", "score > threshold", "3 janelas consecutivas", "até 60 min antes do evento"],
        })
        """
    )

    md(
        """
        ## 2. Descrição dos dados da Forzy

        O SQLite reúne cadastro e telemetria sintética de 20 motores. Há uma leitura por minuto
        de rotação, vibração, temperatura e corrente; `falha` registra normalidade ou uma das
        três falhas conhecidas. O período total é curto (25 horas por motor), uma limitação para
        generalização industrial.
        """
    )
    code(
        """
        data_summary = pd.Series(metrics["data"], name="valor")
        display(data_summary)
        display(pd.DataFrame({"sensor": FEATURES}))
        """
    )

    md(
        """
        ## 3. Análise exploratória dos dados

        A EDA compara distribuições normal/falha, evolução temporal e correlações. Os níveis
        normais diferem por motor, enquanto episódios rotulados formam rampas persistentes.
        Não há valores ausentes nem timestamps duplicados por motor.
        """
    )
    code(
        """
        for name in [
            "s3_01_distribuicao_sensores.png",
            "s3_02_evolucao_temporal.png",
            "s3_03_correlacao.png",
        ]:
            display(Image(filename=str(ROOT / "figuras" / name)))
        """
    )

    md(
        """
        ## 4. Definição do baseline operacional

        Cada motor é calibrado pelas primeiras 30 leituras usando mediana e IQR. O baseline
        estatístico calcula o maior desvio absoluto médio entre sensores. Isolation Forest e
        Autoencoder recebem representações normalizadas; cada threshold é o percentil 99 dos
        scores normais da validação, sem consultar o teste.
        """
    )
    code(
        """
        pd.DataFrame({
            "modelo": list(metrics["thresholds"]),
            "threshold": list(metrics["thresholds"].values()),
            "fonte": metrics["threshold_source"],
        })
        """
    )

    md(
        """
        ## 5. Preparação dos dados

        O split é feito por motor: treino, validação e teste são ativos diferentes. Janelas de
        treino precisam ser totalmente normais e ficar 30 minutos afastadas de qualquer falha
        rotulada. Janelas nunca atravessam motores nem lacunas temporais.
        """
    )
    code(
        """
        display(pd.Series(metrics["split"], name="motores"))
        display(pd.Series(metrics["window_config"], name="valor"))
        print("Shape sequencial:", result.prepared.sequences.shape)
        print("Shape de features agregadas:", result.prepared.summaries.shape)
        print("Janelas usadas no fit/threshold:", metrics["fit_counts"])
        """
    )

    md(
        """
        ## 6. Treinamento do modelo de anomalias

        O **Isolation Forest** usa 24 estatísticas temporais (média, desvio, mínimo, máximo,
        último valor e inclinação por sensor). O **Autoencoder denso** recebe 120 entradas
        (30 × 4), comprime para 16 neurônios e reconstrói a sequência. Seu MAE de reconstrução
        é o score; erro alto indica padrão diferente do normal aprendido.
        """
    )
    code(
        """
        pd.Series(metrics["training_info"], name="valor")
        """
    )

    md(
        """
        ## 7. Avaliação dos resultados

        Avaliamos precision, recall, F1, ROC-AUC, PR-AUC, falsos positivos e matriz de confusão.
        Também medimos recall por evento e antecedência da primeira detecção persistente. PR-AUC
        é especialmente útil porque as anomalias são minoritárias.
        """
    )
    code(
        """
        metric_columns = ["precision", "recall", "f1", "pr_auc", "roc_auc", "false_positive_rate"]
        window_table = pd.DataFrame(metrics["window_metrics"]).T[metric_columns]
        event_table = pd.DataFrame(metrics["event_metrics"]).T
        display(window_table.style.format("{:.3f}"))
        display(event_table)
        """
    )

    md(
        """
        ## 8. Análise dos casos anômalos

        O ranking identifica motores com maior frequência e persistência de alertas. Os erros
        do Autoencoder mostram quais sensores foram mais difíceis de reconstruir; essa é uma
        explicação do modelo, **não uma prova causal** da falha física.
        """
    )
    code(
        """
        display(result.motor_ranking)
        display(result.sensor_ranking)
        display(result.event_details.query("model == 'autoencoder'").head(10))
        """
    )

    md(
        """
        ## 9. Comparação com a Sprint 2

        O Random Forest da Sprint 2 recebe classes conhecidas e é avaliado exatamente nos
        timestamps finais das mesmas janelas. Ele é melhor para reconhecer o catálogo já
        rotulado; os detectores de anomalia procuram qualquer desvio e podem sinalizar antes
        do rótulo. Macro-F1 multiclasse antigo não é comparado diretamente com F1 binário.
        """
    )
    code(
        """
        comparison = window_table.copy()
        comparison["event_recall"] = pd.Series({name: values["event_recall"] for name, values in metrics["event_metrics"].items()})
        comparison["anticipated_events"] = pd.Series({name: values["anticipated_events"] for name, values in metrics["event_metrics"].items()})
        comparison
        """
    )

    md(
        """
        ## 10. Visualização dos resultados

        Scores são mostrados como razão `score / threshold`, permitindo comparar modelos com
        escalas diferentes. Matrizes de confusão, ranking de motores e erros por sensor apoiam
        priorização e investigação dos casos detectados.
        """
    )
    code(
        """
        for name in [
            "s3_04_scores_tempo.png",
            "s3_05_matrizes_confusao.png",
            "s3_06_ranking_motores.png",
            "s3_07_contribuicao_sensores.png",
        ]:
            display(Image(filename=str(ROOT / "figuras" / name)))
        """
    )

    md(
        """
        ## 11. Integração futura com agente conversacional

        A função local abaixo produz um payload com score, severidade, persistência, sensores
        dominantes e explicação. Um agente poderá responder perguntas como “por que o motor 1
        está em alerta?”, preservando os números calculados pelo pipeline.
        """
    )
    code(
        """
        candidate = scored.query("partition == 'test'").sort_values("autoencoder_score").iloc[-1]
        sensor_errors = {feature: candidate[f"ae_error_{feature}"] for feature in FEATURES}
        build_agent_payload(
            motor_id=candidate.motor_id,
            timestamp=candidate.timestamp,
            score=candidate.autoencoder_score,
            threshold=candidate.autoencoder_threshold,
            persistent=candidate.autoencoder_persistent,
            sensor_errors=sensor_errors,
        )
        """
    )

    md(
        """
        ## 12. Código e organização

        O script `src/run_sprint3.py` recria modelo, métricas, CSVs, relatório e figuras.
        A suíte pytest protege partições, calibração, janelas, thresholds, persistência, eventos,
        comparação e payload conversacional. Os artefatos versionados permitem auditoria sem
        executar novamente o treino.

        ### Limitações finais

        - base sintética e horizonte curto;
        - primeiras 30 leituras assumidas como comissionamento saudável;
        - threshold precisa ser recalibrado em dados reais;
        - alerta pré-rótulo pode representar degradação emergente ou falso positivo;
        - sensor dominante não equivale à causa raiz.
        """
    )
    code(
        """
        artifact_paths = [
            ROOT / "models" / "modelo_anomalias.joblib",
            ROOT / "models" / "anomaly_metrics.json",
            ROOT / "results" / "anomaly_scores.csv",
            ROOT / "docs" / "sprint3_report.md",
        ]
        pd.DataFrame({"artefato": [str(path.relative_to(ROOT)) for path in artifact_paths], "existe": [path.exists() for path in artifact_paths]})
        """
    )

    notebook = nbf.v4.new_notebook(cells=cells)
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata["language_info"] = {"name": "python", "version": "3.12"}
    return notebook


def write_notebook(output_path: Path = DEFAULT_OUTPUT) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(build_notebook(), output_path)
    return output_path


if __name__ == "__main__":
    path = write_notebook()
    print(f"Notebook gerado em {path}")
