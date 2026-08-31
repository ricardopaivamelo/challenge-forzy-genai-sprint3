"""Aplicação demonstrável da governança de decisão da Forzy."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.demo_scenarios import build_demo_scenarios, evaluate_demo_scenario
from src.dashboard_data import build_contract_rows, build_handoff_record
from src.governance_contracts import load_metric_contracts


ROOT = Path(__file__).resolve().parent
CONTRACTS = load_metric_contracts(ROOT / "config" / "metric_contracts.json")
SCENARIOS = build_demo_scenarios()


THEME_PALETTES = {
    "Escuro": {
        "background": "#0E1117",
        "sidebar": "#161B22",
        "surface": "#1E2530",
        "surface_border": "#354052",
        "text": "#F3F4F6",
        "muted": "#B8C0CC",
        "header": "rgba(14, 17, 23, 0.92)",
    },
    "Claro": {
        "background": "#F7F8FA",
        "sidebar": "#EEF1F5",
        "surface": "#FFFFFF",
        "surface_border": "#D9DDE5",
        "text": "#1F2937",
        "muted": "#536072",
        "header": "rgba(247, 248, 250, 0.92)",
    },
}


def apply_theme(theme_name: str) -> None:
    """Aplica a paleta escolhida aos principais componentes do dashboard."""

    palette = THEME_PALETTES[theme_name]
    st.markdown(
        f"""
        <style>
        .stApp, [data-testid="stAppViewContainer"] {{
            background: {palette['background']};
            color: {palette['text']};
        }}
        [data-testid="stHeader"] {{ background: {palette['header']}; }}
        [data-testid="stSidebar"] > div:first-child {{
            background: {palette['sidebar']};
        }}
        div[data-testid="stMetric"] {{
            background: {palette['surface']};
            border: 1px solid {palette['surface_border']};
            border-radius: 12px;
            padding: 14px 16px;
        }}
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        [data-testid="stMetricDelta"],
        [data-testid="stMarkdownContainer"],
        [data-testid="stCaptionContainer"] {{
            color: {palette['text']};
        }}
        [data-testid="stCaptionContainer"] {{ color: {palette['muted']}; }}
        [data-testid="stDataFrame"] {{
            border: 1px solid {palette['surface_border']};
            border-radius: 10px;
            overflow: hidden;
        }}
        [data-baseweb="select"] > div,
        .stSelectbox .react-aria-ComboBox > div,
        [data-testid="stNumberInput"] input,
        [data-testid="stNumberInput"] button {{
            background: {palette['surface']};
            border-color: {palette['surface_border']};
            color: {palette['text']};
        }}
        [data-baseweb="select"] *,
        .stSelectbox .react-aria-ComboBox *,
        [data-testid="stNumberInput"] * {{ color: {palette['text']}; }}
        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="popover"] [role="option"] {{
            background: {palette['surface']};
            color: {palette['text']};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Forzy | Governança da Decisão",
    page_icon="⚙️",
    layout="wide",
)
theme_name = st.sidebar.radio(
    "Tema",
    ["Escuro", "Claro"],
    horizontal=True,
    key="dashboard_theme",
)
apply_theme(theme_name)

st.title("Forzy | Governança da Decisão")
st.caption(
    "Challenge Sprint 3 · Thresholds, Circuit Breaker e supervisão humana "
    "aplicados ao protótipo de manutenção preditiva."
)

scenario_options = list(SCENARIOS)
requested_scenario = st.query_params.get("scenario")
scenario_index = (
    scenario_options.index(requested_scenario)
    if requested_scenario in scenario_options
    else 0
)
scenario_name = st.sidebar.selectbox(
    "Cenário demonstrado", scenario_options, index=scenario_index
)
motor_id = int(st.sidebar.number_input("Motor", min_value=1, max_value=20, value=7))
manual = st.sidebar.toggle("Editar leituras manualmente", value=False)
scenario = SCENARIOS[scenario_name]

if manual:
    st.sidebar.markdown("#### Leituras")
    defaults = {
        "temperatura_c": scenario.readings.get("temperatura_c", 70.0),
        "vibracao_mm_s": scenario.readings.get("vibracao_mm_s", 2.0),
        "aceleracao_g": scenario.readings.get("aceleracao_g", 0.08),
    }
    numeric_defaults = {
        field: float(value) if isinstance(value, (int, float)) else 0.0
        for field, value in defaults.items()
    }
    readings = {
        "temperatura_c": st.sidebar.number_input(
            "Temperatura (°C)", value=numeric_defaults["temperatura_c"], step=1.0
        ),
        "vibracao_mm_s": st.sidebar.number_input(
            "Vibração RMS (mm/s)", value=numeric_defaults["vibracao_mm_s"], step=0.1
        ),
        "aceleracao_g": st.sidebar.number_input(
            "Aceleração (g)", value=numeric_defaults["aceleracao_g"], step=0.01
        ),
    }
    scenario = replace(
        scenario,
        readings=readings,
        score=st.sidebar.number_input("Score do Autoencoder", value=scenario.score, step=0.05),
        persistent=st.sidebar.checkbox("Persistente por três janelas", scenario.persistent),
        classifier_confidence=st.sidebar.slider(
            "Confiança do classificador",
            min_value=0.0,
            max_value=1.0,
            value=scenario.classifier_confidence,
            step=0.01,
        ),
    )

decision = evaluate_demo_scenario(scenario, CONTRACTS, motor_id=motor_id)

st.subheader(scenario_name)
st.write(scenario.description)

columns = st.columns(3)
for column, field in zip(columns, ("temperatura_c", "vibracao_mm_s", "aceleracao_g")):
    contract = CONTRACTS[field]
    value = scenario.readings.get(field)
    rendered = f"{value} {contract.unit}" if isinstance(value, (int, float)) else str(value)
    state = decision.sensor_states.get(field, "invalid")
    column.metric(contract.label, rendered, delta=state.upper(), delta_color="off")

if decision.status == "normal":
    st.success("DECISÃO: NORMAL — monitoramento de rotina autorizado.")
elif decision.status == "attention":
    st.warning("DECISÃO: ATTENTION — acompanhar tendência sem emitir parada.")
elif decision.status == "alert":
    st.error("DECISÃO: ALERT — inspeção humana solicitada; parada automática proibida.")
else:
    st.error("DECISÃO: BLOCKED — Circuit Breaker aberto; alerta decisório travado.")
    for reason in decision.breaker_reasons:
        st.error(reason)

left, right = st.columns([1.2, 1])
with left:
    st.markdown("### Metric Contracts")
    contract_rows = build_contract_rows(
        contracts=CONTRACTS,
        readings=scenario.readings,
        sensor_states=decision.sensor_states,
    )
    contract_frame = pd.DataFrame(contract_rows)
    table_palette = THEME_PALETTES[theme_name]
    styled_contracts = contract_frame.style.set_properties(
        **{
            "background-color": table_palette["surface"],
            "color": table_palette["text"],
            "border-color": table_palette["surface_border"],
        }
    ).set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("background-color", table_palette["sidebar"]),
                    ("color", table_palette["text"]),
                ],
            }
        ]
    )
    st.table(styled_contracts.hide(axis="index"))

    normalized = []
    for field, contract in CONTRACTS.items():
        value = scenario.readings.get(field)
        if isinstance(value, (int, float)):
            normalized.append(
                {
                    "Métrica": contract.label,
                    "Valor / limite crítico": float(value) / contract.critical_min,
                }
            )
    if normalized:
        chart_palette = THEME_PALETTES[theme_name]
        chart = (
            alt.Chart(pd.DataFrame(normalized))
            .mark_bar(color="#4EA1FF")
            .encode(
                x=alt.X("Métrica:N", sort=None, title=None),
                y=alt.Y("Valor / limite crítico:Q", title="Proporção do limite crítico"),
                tooltip=["Métrica:N", alt.Tooltip("Valor / limite crítico:Q", format=".3f")],
            )
            .properties(background=chart_palette["surface"])
            .configure_axis(
                domainColor=chart_palette["surface_border"],
                gridColor=chart_palette["surface_border"],
                labelColor=chart_palette["text"],
                titleColor=chart_palette["text"],
            )
            .configure_view(stroke=chart_palette["surface_border"])
        )
        st.altair_chart(chart, width="stretch")

with right:
    st.markdown("### Decisão auditável")
    st.metric("Score / threshold", f"{decision.anomaly_score:.4f} / {decision.model_threshold:.4f}")
    st.metric("Persistência", "3 janelas" if decision.persistent else "Não confirmada")
    st.metric(
        "Circuit Breaker",
        "ABERTO" if decision.circuit_breaker_open else "FECHADO",
    )
    st.info(decision.automatic_action)

if decision.requires_human:
    st.markdown("### Handoff humano")
    st.write("Destinatário: **Engenheiro de Manutenção**")
    human_decision = st.radio(
        "Decisão do especialista",
        ["Pendente", "Validado", "Rejeitado"],
        horizontal=True,
    )
    justification = st.text_area(
        "Justificativa autoral do especialista",
        placeholder="Registrar contexto de planta, ruídos externos e decisão tomada.",
    )
    if st.button("Registrar validação humana"):
        if human_decision == "Pendente" or not justification.strip():
            st.warning("Selecione Validado/Rejeitado e registre uma justificativa.")
        else:
            event_key = decision.timestamp.replace("-", "").replace(":", "")
            event_key = event_key.replace("+0000", "Z")
            st.session_state["last_handoff"] = build_handoff_record(
                alert_id=f"ALT-MTR-{motor_id:03d}-{event_key}",
                motor_id=motor_id,
                scenario_name=scenario_name,
                decision=human_decision,
                justification=justification.strip(),
                recorded_at=datetime.now(timezone.utc),
                readings=scenario.readings,
                anomaly_score=decision.anomaly_score,
                model_threshold=decision.model_threshold,
                classifier_confidence=decision.classifier_confidence,
                minimum_confidence=0.85,
                breaker_reasons=decision.breaker_reasons,
                contract_versions={
                    field: contract.version for field, contract in CONTRACTS.items()
                },
            )
            st.success("Validação humana registrada nesta sessão de demonstração.")
    if "last_handoff" in st.session_state:
        st.markdown("#### Último registro auditável da sessão")
        st.json(st.session_state["last_handoff"], expanded=False)

st.divider()
st.caption(
    "Protótipo acadêmico com dados sintéticos. A aceleração é simulada e os limites exigem "
    "calibração industrial. A matriz de supervisão e a conclusão refletem as decisões "
    "autorais aprovadas pelo grupo."
)
