import json

import pytest

from src.governance_contracts import MetricContract, load_metric_contracts


def make_contract() -> MetricContract:
    return MetricContract(
        metric_id="temperature",
        field="temperatura_c",
        label="Temperatura",
        unit="°C",
        valid_min=0.0,
        valid_max=200.0,
        attention_min=90.0,
        critical_min=100.0,
        frequency_seconds=60,
        owner="Engenharia de Manutenção",
        version="1.0",
        threshold_source="Hipótese interna a validar na planta",
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (89.999, "normal"),
        (90.0, "attention"),
        (99.999, "attention"),
        (100.0, "critical"),
    ],
)
def test_contract_classifies_boundary_values(value, expected):
    assert make_contract().classify(value).state == expected


@pytest.mark.parametrize("value", [-0.001, 200.001])
def test_contract_rejects_values_outside_physical_domain(value):
    with pytest.raises(ValueError, match="fora do domínio físico"):
        make_contract().classify(value)


def test_contract_rejects_non_finite_values():
    with pytest.raises(ValueError, match="finito"):
        make_contract().classify(float("nan"))


def test_load_contracts_indexes_three_required_metrics(tmp_path):
    payload = {
        "contracts": [
            {
                "metric_id": metric_id,
                "field": field,
                "label": label,
                "unit": unit,
                "valid_min": 0,
                "valid_max": 200,
                "attention_min": 10,
                "critical_min": 20,
                "frequency_seconds": 60,
                "owner": "Engenharia de Manutenção",
                "version": "1.0",
                "threshold_source": "Teste controlado",
            }
            for metric_id, field, label, unit in [
                ("temperature", "temperatura_c", "Temperatura", "°C"),
                ("vibration", "vibracao_mm_s", "Vibração RMS", "mm/s"),
                ("acceleration", "aceleracao_g", "Aceleração", "g"),
            ]
        ]
    }
    path = tmp_path / "contracts.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    contracts = load_metric_contracts(path)

    assert set(contracts) == {"temperatura_c", "vibracao_mm_s", "aceleracao_g"}
    assert contracts["aceleracao_g"].unit == "g"


def test_load_contracts_rejects_inverted_thresholds(tmp_path):
    payload = {
        "contracts": [
            {
                "metric_id": "temperature",
                "field": "temperatura_c",
                "label": "Temperatura",
                "unit": "°C",
                "valid_min": 0,
                "valid_max": 200,
                "attention_min": 100,
                "critical_min": 90,
                "frequency_seconds": 60,
                "owner": "Engenharia de Manutenção",
                "version": "1.0",
                "threshold_source": "Teste controlado",
            }
        ]
    }
    path = tmp_path / "contracts.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="ordem dos limites"):
        load_metric_contracts(path)
