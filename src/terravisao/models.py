"""Contratos de dados entre módulos (docs/07). Sem dependências geoespaciais pesadas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import numpy as np

from .config import Level, Target


@dataclass
class AnalysisRequest:
    geometry: dict[str, Any]  # GeoJSON Polygon/MultiPolygon em WGS84
    targets: list[Target]
    date_from: date | None = None
    date_to: date | None = None
    max_cloud_pct: float = 20.0
    weights_override: dict[str, dict[str, float]] | None = None
    name: str | None = None


@dataclass
class Layer:
    name: str
    array: np.ndarray  # 2D float32, NaN onde inválido
    source: str
    valid_fraction: float
    status: str = "ok"  # ok | partial | unavailable
    unit: str | None = None
    note: str | None = None


@dataclass
class Unavailable:
    """Falha de uma fonte como valor: o pipeline continua e regista aviso."""

    source: str
    reason: str


@dataclass
class Zone:
    id: str
    target: Target
    area_km2: float
    mean_score: float
    max_score: float
    contributions: dict[str, float] = field(default_factory=dict)
    recommendation: str = ""
    geometry: dict[str, Any] | None = None


@dataclass
class TargetResult:
    target: Target
    final_class: Level
    confidence: Level
    score: np.ndarray
    classes: np.ndarray  # 0 baixa, 1 média, 2 alta
    area_by_class_km2: dict[str, float]
    zones: list[Zone] = field(default_factory=list)
