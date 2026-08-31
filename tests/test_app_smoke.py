from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_renders_normal_scenario_without_exception():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=10).run()

    assert not app.exception
    assert app.title[0].value == "Forzy | Governança da Decisão"
    assert any("NORMAL" in item.value for item in app.success)


def test_dashboard_exposes_circuit_breaker_scenario():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=10).run()

    app.selectbox[0].select("Circuit Breaker por dado inválido").run()

    assert not app.exception
    assert any("BLOCKED" in item.value for item in app.error)
    assert any("não numérico" in item.value.lower() for item in app.error)


def test_dashboard_exposes_handoff_for_confirmed_anomaly():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=10).run()

    app.selectbox[0].select("Anomalia confirmada").run()

    assert not app.exception
    assert any("ALERT" in item.value for item in app.error)
    assert app.radio[0].label == "Decisão do especialista"


def test_dashboard_accepts_scenario_query_parameter_for_evidence_capture():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=10)
    app.query_params["scenario"] = "Anomalia confirmada"

    app.run()

    assert not app.exception
    assert app.selectbox[0].value == "Anomalia confirmada"
    assert any("ALERT" in item.value for item in app.error)


def test_dashboard_defaults_to_dark_theme_and_allows_switching_to_light():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=10).run()

    assert not app.exception
    assert app.radio[0].label == "Tema"
    assert app.radio[0].value == "Escuro"

    app.radio[0].set_value("Claro").run()

    assert not app.exception
    assert app.radio[0].value == "Claro"
