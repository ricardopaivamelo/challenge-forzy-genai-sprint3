"""Contratos versionados para métricas operacionais da Forzy."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class SensorAssessment:
    field: str
    label: str
    unit: str
    value: float
    state: str
    threshold_triggered: float | None


@dataclass(frozen=True)
class MetricContract:
    metric_id: str
    field: str
    label: str
    unit: str
    valid_min: float
    valid_max: float
    attention_min: float
    critical_min: float
    frequency_seconds: int
    owner: str
    version: str
    threshold_source: str
    description: str = ""
    persistence_windows: int = 3
    automatic_action: str = "Registrar e solicitar inspeção técnica."

    def __post_init__(self) -> None:
        limits = (
            self.valid_min,
            self.attention_min,
            self.critical_min,
            self.valid_max,
        )
        if not all(math.isfinite(float(value)) for value in limits):
            raise ValueError(f"{self.field}: limites devem ser finitos")
        if not self.valid_min <= self.attention_min < self.critical_min <= self.valid_max:
            raise ValueError(f"{self.field}: ordem dos limites é inválida")
        if self.frequency_seconds <= 0 or self.persistence_windows <= 0:
            raise ValueError(f"{self.field}: frequência e persistência devem ser positivas")

    def classify(self, value: float) -> SensorAssessment:
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"{self.field}: valor deve ser finito")
        if numeric < self.valid_min or numeric > self.valid_max:
            raise ValueError(
                f"{self.field}: valor {numeric} fora do domínio físico "
                f"[{self.valid_min}, {self.valid_max}]"
            )
        if numeric >= self.critical_min:
            state = "critical"
            threshold = self.critical_min
        elif numeric >= self.attention_min:
            state = "attention"
            threshold = self.attention_min
        else:
            state = "normal"
            threshold = None
        return SensorAssessment(
            field=self.field,
            label=self.label,
            unit=self.unit,
            value=numeric,
            state=state,
            threshold_triggered=threshold,
        )


def load_metric_contracts(path: str | Path) -> dict[str, MetricContract]:
    """Carrega contratos JSON e os indexa pelo campo recebido do sensor."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    entries = payload.get("contracts")
    if not isinstance(entries, list) or not entries:
        raise ValueError("arquivo deve conter uma lista não vazia em 'contracts'")
    contracts = [MetricContract(**entry) for entry in entries]
    indexed = {contract.field: contract for contract in contracts}
    if len(indexed) != len(contracts):
        raise ValueError("campos de contratos devem ser únicos")
    return indexed
