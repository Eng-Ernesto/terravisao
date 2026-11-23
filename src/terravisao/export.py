"""Exportação: GeoTIFF (pontuação/classes), GeoJSON (zonas, bacias) e run.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
import shapely
from pyproj import Transformer
from rasterio.features import shapes
from shapely.geometry import mapping, shape

from .models import AnalysisResult
from .pipeline import summary


def _write_tif(path: Path, arr: np.ndarray, result: AnalysisResult, nodata: float | int) -> None:
    g = result.grid
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=arr.shape[0],
        width=arr.shape[1],
        count=1,
        dtype=arr.dtype,
        crs=g.crs,
        transform=g.transform,
        nodata=nodata,
        compress="deflate",
    ) as dst:
        dst.write(arr, 1)


def _to_wgs84(geom: shapely.Geometry, epsg: int) -> shapely.Geometry:
    t = Transformer.from_crs(epsg, 4326, always_xy=True)

    def project(coords: np.ndarray) -> np.ndarray:
        x, y = t.transform(coords[:, 0], coords[:, 1])
        return np.column_stack([x, y])

    return shapely.transform(geom, project)


def _polygonize(
    labels: np.ndarray, result: AnalysisResult, names: dict[int, str]
) -> dict[str, Any]:
    feats = []
    for geom, val in shapes(
        labels.astype(np.int32), mask=labels > 0, transform=result.grid.transform
    ):
        poly = _to_wgs84(shape(geom), result.grid.epsg)
        feats.append(
            {
                "type": "Feature",
                "geometry": mapping(poly),  # type: ignore[arg-type]
                "properties": {"id": names.get(int(val), str(int(val)))},
            }
        )
    return {"type": "FeatureCollection", "features": feats}


def export_all(result: AnalysisResult, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for target, tr in result.targets.items():
        p = out_dir / f"score_{target.value}.tif"
        _write_tif(p, tr.score.astype(np.float32), result, np.nan)
        written.append(p)
        p = out_dir / f"class_{target.value}.tif"
        _write_tif(p, tr.classes, result, 255)
        written.append(p)
        labels = result.zone_labels[target]
        names = {rank + 1: z.id for rank, z in enumerate(tr.zones)}
        zones = _polygonize(labels, result, names)
        for feat in zones["features"]:
            z = next(z for z in tr.zones if z.id == feat["properties"]["id"])
            feat["properties"].update(
                area_km2=round(z.area_km2, 3),
                mean_score=round(z.mean_score, 3),
                recommendation=z.recommendation,
                contributions={k: round(v, 3) for k, v in z.contributions.items()},
            )
        p = out_dir / f"zones_{target.value}.geojson"
        p.write_text(json.dumps(zones, ensure_ascii=False), encoding="utf-8")
        written.append(p)
    for name, arr in result.thematic.items():
        p = out_dir / f"layer_{name}.tif"
        _write_tif(p, arr.astype(np.float32), result, np.nan)
        written.append(p)
    p = out_dir / "run.json"
    meta = {
        "provenance": result.provenance.__dict__,
        "summary": summary(result),
        "request": {
            "targets": [t.value for t in result.request.targets],
            "geometry": result.request.geometry,
            "name": result.request.name,
        },
    }
    p.write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    written.append(p)
    return written
