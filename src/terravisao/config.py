"""Configuração central. Pesos e limiares são pontos de partida [A CALIBRAR] (docs/05)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Target(StrEnum):
    """Minerais críticos para a transição energética (ADR-23)."""

    REE = "terras_raras"
    COPPER = "cobre"
    LITHIUM = "litio"
    MANGANESE = "manganes"


class Level(StrEnum):
    LOW = "baixa"
    MEDIUM = "media"
    HIGH = "alta"


# Pesos por alvo; soma = 1 por alvo (verificado em testes). Pontos de partida [A CALIBRAR] com o
# geofísico. O satélite só vê contexto favorável (alteração, óxidos, estruturas), não o mineral.
DEFAULT_WEIGHTS: dict[Target, dict[str, float]] = {
    # Carbonatitos: halos de óxidos e alteração argilosa, estruturas circulares e falhas profundas.
    Target.REE: {
        "iron_oxide": 0.20,
        "ferrous": 0.05,
        "clay": 0.20,
        "lithology": 0.25,
        "lineament_density": 0.25,
        "slope_inv": 0.05,
    },
    # Pórfiros e cinturões de cobre: alteração argilosa/fílica, óxidos (gossans), estruturas.
    Target.COPPER: {
        "iron_oxide": 0.15,
        "clay": 0.25,
        "lithology": 0.30,
        "lineament_density": 0.25,
        "slope_inv": 0.05,
    },
    # Pegmatitos: controlo estrutural e litológico forte; assinatura espectral fraca (experimental).
    Target.LITHIUM: {
        "iron_oxide": 0.10,
        "clay": 0.25,
        "lithology": 0.30,
        "lineament_density": 0.30,
        "slope_inv": 0.05,
    },
    # Manganês (e ferro associado): óxidos férricos e ferrosos, litologia sedimentar/metamórfica.
    Target.MANGANESE: {
        "iron_oxide": 0.25,
        "ferrous": 0.25,
        "lithology": 0.30,
        "lineament_density": 0.15,
        "slope_inv": 0.05,
    },
}


RECOMMENDATIONS: dict[Target, str] = {
    Target.REE: "Radiometria (Th, U) e magnetometria; geoquímica de solo (TREO, NdPr).",
    Target.COPPER: "Polarização induzida (IP), magnetometria e geoquímica de solo.",
    Target.LITHIUM: "Mapeamento de pegmatitos no campo; geoquímica de solo e rocha (Li, Cs, Ta).",
    Target.MANGANESE: "Magnetometria e gravimetria; amostragem de superfície dos óxidos.",
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
    # Suavização da pontuação antes de classificar (m). 0 desliga.
    score_smoothing_m: float = 100.0
    # 5 ha: menor mancha que vale a pena visitar. [A CALIBRAR] com o geofísico.
    min_zone_area_km2: float = 0.05
    # Zona mínima para o alvo ser classificado como Alta no terreno todo (50 ha).
    final_high_zone_km2: float = 0.5
    weights: dict[Target, dict[str, float]] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))


SETTINGS = Settings()
