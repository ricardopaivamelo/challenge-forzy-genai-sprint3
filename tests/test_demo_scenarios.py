from pathlib import Path

from src.demo_scenarios import build_demo_scenarios, evaluate_demo_scenario
from src.governance_contracts import load_metric_contracts


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = load_metric_contracts(ROOT / "config" / "metric_contracts.json")


def test_five_demo_scenarios_cover_required_governance_states():
    scenarios = build_demo_scenarios()

    assert list(scenarios) == [
        "Operação normal",
        "Faixa de atenção",
        "Anomalia confirmada",
        "Circuit Breaker por dado inválido",
        "Handoff por baixa confiança",
    ]
    statuses = {
        name: evaluate_demo_scenario(scenario, CONTRACTS).status
        for name, scenario in scenarios.items()
    }
    assert statuses == {
        "Operação normal": "normal",
        "Faixa de atenção": "attention",
        "Anomalia confirmada": "alert",
        "Circuit Breaker por dado inválido": "blocked",
        "Handoff por baixa confiança": "blocked",
    }


def test_invalid_data_scenario_exposes_breaker_reason():
    scenario = build_demo_scenarios()["Circuit Breaker por dado inválido"]

    decision = evaluate_demo_scenario(scenario, CONTRACTS)

    assert decision.circuit_breaker_open is True
    assert any("não numérico" in reason.lower() for reason in decision.breaker_reasons)
