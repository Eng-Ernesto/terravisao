"""Configuração central. Pesos e limiares são pontos de partida [A CALIBRAR] (docs/05)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Target(StrEnum):
    IRON = "ferro"
    COPPER = "cobre"
    GOLD = "ouro"
    WATER = "agua"


class Level(StrEnum):
    LOW = "baixa"
    MEDIUM = "media"
    HIGH = "alta"


# Pesos por alvo; soma = 1 por alvo (verificado em testes).
DEFAULT_WEIGHTS: dict[Target, dict[str, float]] = {
    Target.IRON: {
        "iron_oxide": 0.35,
        "ferrous": 0.10,
        "clay": 0.10,
        "lithology": 0.30,
        "lineament_density": 0.10,
        "slope_inv": 0.05,
    },
    Target.COPPER: {
        "iron_oxide": 0.15,
        "clay": 0.25,
        "lithology": 0.30,
        "lineament_density": 0.25,
        "slope_inv": 0.05,
    },
    Target.GOLD: {
        "iron_oxide": 0.20,
        "clay": 0.20,
        "lithology": 0.25,
        "lineament_density": 0.30,
        "slope_inv": 0.05,
    },
    Target.WATER: {
        "lithology": 0.25,
        "lineament_density": 0.25,
        "slope_inv": 0.15,
        "twi": 0.15,
        "drainage_density_inv": 0.10,
        "ndvi": 0.10,
    },
}


RECOMMENDATIONS: dict[Target, str] = {
    Target.IRON: "Magnetometria e amostragem de superfície.",
    Target.COPPER: "Polarização induzida (IP), magnetometria e geoquímica de solo.",
    Target.GOLD: "Geoquímica de solo/sedimento de corrente, magnetometria e IP.",
    Target.WATER: "Resistividade (SEV/tomografia); verificar furos existentes na zona.",
}


@dataclass(frozen=True)
class Settings:
    max_area_km2: float = 2500.0
    grid_resolution_m: int = 20
    season_months: tuple[int, ...] = (5, 6, 7, 8, 9)
    ndvi_mask: float = 0.4
    percentiles: tuple[float, float] = (2.0, 98.0)
    threshold_medium: float = 0.40
    threshold_high: float = 0.65
    min_zone_area_km2: float = 0.5
    weights: dict[Target, dict[str, float]] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))


SETTINGS = Settings()
