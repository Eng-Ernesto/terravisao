"""Validação da área de interesse e escolha do fuso UTM."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from .config import SETTINGS

# Caixa envolvente aproximada de Angola (inclui Cabinda). A validação final usa a fronteira
# real em data/reference/angola_boundary.geojson (T-102).
ANGOLA_BBOX = (11.5, -18.1, 24.1, -4.3)  # lon_min, lat_min, lon_max, lat_max


class AoiError(ValueError):
    """Terreno inválido; a mensagem é mostrável ao utilizador."""


def utm_epsg(lon: float, lat: float) -> int:
    """EPSG do fuso UTM WGS84 para um ponto (hemisfério sul: 327xx)."""
    zone = int(math.floor((lon + 180) / 6)) + 1
    return (32600 if lat >= 0 else 32700) + zone


def area_km2(geom: BaseGeometry) -> float:
    c = geom.centroid
    to_utm = Transformer.from_crs(4326, utm_epsg(c.x, c.y), always_xy=True)

    def project(coords: np.ndarray) -> np.ndarray:
        x, y = to_utm.transform(coords[:, 0], coords[:, 1])
        return np.column_stack([x, y])

    return float(shapely.transform(geom, project).area / 1e6)


def validate_aoi(geojson: dict[str, Any], max_area_km2: float | None = None) -> BaseGeometry:
    """Devolve a geometria validada ou levanta AoiError com mensagem clara."""
    limit = SETTINGS.max_area_km2 if max_area_km2 is None else max_area_km2
    try:
        geom = shape(geojson)
    except Exception as exc:  # geometria mal formada
        raise AoiError("A geometria do terreno não é válida.") from exc

    if geom.is_empty or geom.geom_type not in {"Polygon", "MultiPolygon"}:
        raise AoiError("O terreno tem de ser um polígono.")
    if not geom.is_valid:
        raise AoiError("O polígono tem auto-intersecções. Redesenhe o terreno.")

    lon_min, lat_min, lon_max, lat_max = ANGOLA_BBOX
    minx, miny, maxx, maxy = geom.bounds
    if minx < lon_min or maxx > lon_max or miny < lat_min or maxy > lat_max:
        raise AoiError("O terreno tem de estar dentro de Angola.")

    area = area_km2(geom)
    if area > limit:
        raise AoiError(f"O terreno tem {area:,.0f} km². O máximo é {limit:,.0f} km².")
    return geom
