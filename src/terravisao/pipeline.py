"""Orquestrador: AnalysisRequest -> AnalysisResult (docs/03 §2)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

import numpy as np

from . import __version__, indices, scoring, terrain
from .aoi import validate_aoi
from .config import RECOMMENDATIONS, SETTINGS, Level, Target
from .grid import Grid
from .ingest.dem import fetch_dem
from .ingest.geology import lithology_favorability
from .ingest.sentinel2 import fetch_sentinel2
from .models import (
    AnalysisRequest,
    AnalysisResult,
    Provenance,
    TargetResult,
    Unavailable,
)
from .zones import extract_zones

Progress = Callable[[str, float], None]


def final_class(classes: np.ndarray, largest_zone_km2: float, aoi: np.ndarray) -> Level:
    """Classe final do alvo (docs/05 §7).

    Alta: zona grande (>= final_high_zone_km2) ou >= 10 % da área em classe Alta.
    Média: existe alguma zona, ou >= 20 % da área em Média+Alta.
    """
    total = max(int(aoi.sum()), 1)
    high = float(((classes == 2) & aoi).sum()) / total
    mid_up = float(((classes >= 1) & (classes != 255) & aoi).sum()) / total
    if largest_zone_km2 >= SETTINGS.final_high_zone_km2 or high >= 0.10:
        return Level.HIGH
    if largest_zone_km2 > 0 or mid_up >= 0.20:
        return Level.MEDIUM
    return Level.LOW


def confidence(valid_fraction: float, has_geology: bool) -> Level:
    if valid_fraction < 0.5:
        return Level.LOW
    if valid_fraction >= 0.8 and has_geology:
        return Level.HIGH
    return Level.MEDIUM


def run(request: AnalysisRequest, progress: Progress | None = None) -> AnalysisResult:
    def step(msg: str, frac: float) -> None:
        if progress:
            progress(msg, frac)

    warnings: list[str] = []
    geom = validate_aoi(request.geometry)
    grid = Grid.from_aoi(geom, SETTINGS.grid_resolution_m, buffer_m=1000.0)
    aoi = np.asarray(grid.mask_of(geom), dtype=bool)
    res = grid.resolution

    step("Imagens Sentinel-2", 0.05)
    s2 = fetch_sentinel2(
        grid,
        request.date_from,
        request.date_to,
        request.max_cloud_pct,
        SETTINGS.season_months,
        max_scenes=6,
    )
    step("Modelo de elevação", 0.45)
    dem = fetch_dem(grid)

    raw: dict[str, np.ndarray] = {}
    thematic: dict[str, np.ndarray] = {}
    scenes: dict[str, list[str]] = {}
    quality: dict[str, float] = {}

    if isinstance(s2, Unavailable):
        warnings.append(s2.reason)
    else:
        step("Índices espectrais", 0.55)
        b = s2.bands
        veg = indices.ndvi(b["nir"], b["red"])
        dense_veg = veg > SETTINGS.ndvi_mask
        # Se a máscara de vegetação remover quase tudo, não a aplicar e avisar.
        apply_mask = float((~dense_veg & np.isfinite(veg)).mean()) >= 0.2
        if not apply_mask:
            warnings.append(
                "Vegetação densa em quase toda a área: índices espectrais pouco fiáveis."
            )
        for name, arr in {
            "iron_oxide": indices.iron_oxide(b["red"], b["blue"]),
            "ferrous": indices.ferrous(b["swir16"], b["nir08"]),
            "clay": indices.clay(b["swir16"], b["swir22"]),
        }.items():
            if apply_mask:
                arr = np.where(dense_veg, np.nan, arr)
            thematic[name] = arr
            raw[name] = scoring.normalize(arr)
        thematic["ndvi"] = veg
        raw["ndvi"] = scoring.normalize(veg)
        scenes["sentinel2"] = s2.scene_ids
        quality["sentinel2"] = s2.valid_fraction

    segments: list[Any] = []
    basin_labels = np.zeros(grid.shape, dtype=np.int32)
    if isinstance(dem, Unavailable):
        warnings.append(dem.reason)
    else:
        step("Terreno e drenagem", 0.7)
        slope = terrain.slope_deg(dem, res)
        hyd = terrain.flow(dem)
        streams = terrain.stream_mask(hyd.accumulation, res)
        segments = terrain.lineaments(dem, res)
        thematic.update(
            elevation=dem,
            slope=slope,
            hillshade=terrain.hillshade(dem, res),
            streams=streams.astype(np.float32),
        )
        raw["slope_inv"] = scoring.normalize(slope, invert=True)
        raw["twi"] = scoring.normalize(terrain.twi(hyd.accumulation, slope, res))
        raw["drainage_density_inv"] = scoring.normalize(terrain.density(streams, res), invert=True)
        raw["lineament_density"] = scoring.normalize(
            terrain.lineament_density(segments, grid.shape, res)
        )
        basin_labels = terrain.basins(hyd, res)
        quality["dem"] = float(np.isfinite(dem).mean())

    step("Pontuação por alvo", 0.85)
    targets: dict[Target, TargetResult] = {}
    zone_labels: dict[Target, np.ndarray] = {}
    for target in request.targets:
        weights = (request.weights_override or {}).get(target.value) or SETTINGS.weights[target]
        layers = dict(raw)
        litho = lithology_favorability(grid, target, column="LITHOLOGY")
        has_geology = not isinstance(litho, Unavailable)
        if isinstance(litho, Unavailable):
            warnings.append(f"Geologia indisponível ({target.value}): {litho.reason}")
        else:
            layers["lithology"] = litho
        if not any(k in layers for k in weights):
            warnings.append(f"Sem camadas disponíveis para {target.value}.")
            continue
        score = scoring.weighted_score(layers, weights)
        score = scoring.smooth(score, SETTINGS.score_smoothing_m / res)
        score = np.where(aoi, score, np.nan).astype(np.float32)
        classes = scoring.classify(score, SETTINGS.threshold_medium, SETTINGS.threshold_high)
        classes = np.where(aoi, classes, 255).astype(np.uint8)
        zones, labels = extract_zones(
            classes,
            score,
            layers,
            weights,
            target,
            grid.pixel_area_km2,
            SETTINGS.min_zone_area_km2,
            RECOMMENDATIONS[target],
        )
        pa = grid.pixel_area_km2
        area_by_class = {
            lvl.value: float(((classes == code) & aoi).sum() * pa)
            for code, lvl in enumerate([Level.LOW, Level.MEDIUM, Level.HIGH])
        }
        valid = float(np.mean(list(quality.values()))) if quality else 0.0
        targets[target] = TargetResult(
            target=target,
            final_class=final_class(classes, max((z.area_km2 for z in zones), default=0.0), aoi),
            confidence=confidence(valid, has_geology),
            score=score,
            classes=classes,
            area_by_class_km2=area_by_class,
            zones=zones,
        )
        zone_labels[target] = labels

    step("Concluído", 1.0)
    prov = Provenance(
        pipeline_version=__version__,
        created_at=datetime.now(UTC).isoformat(),
        scenes=scenes,
        config_snapshot={k: v for k, v in asdict(SETTINGS).items() if k != "weights"},
        layer_quality=quality,
    )
    return AnalysisResult(
        request=request,
        grid=grid,
        aoi_mask=aoi,
        thematic=thematic,
        lineaments=segments,
        basins=basin_labels,
        targets=targets,
        zone_labels=zone_labels,
        provenance=prov,
        warnings=warnings,
    )


def summary(result: AnalysisResult) -> dict[str, Any]:
    out: dict[str, Any] = {"warnings": result.warnings, "targets": {}}
    for t, r in result.targets.items():
        out["targets"][t.value] = {
            "classe_final": r.final_class.value,
            "confianca": r.confidence.value,
            "area_por_classe_km2": {k: round(v, 3) for k, v in r.area_by_class_km2.items()},
            "zonas": [
                {
                    "id": z.id,
                    "area_km2": round(z.area_km2, 3),
                    "score_medio": round(z.mean_score, 3),
                }
                for z in r.zones
            ],
        }
    return out
