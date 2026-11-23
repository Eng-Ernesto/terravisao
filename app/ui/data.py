"""Leitura de resultados já calculados (pasta de exportação do pipeline)."""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from matplotlib import colormaps
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from pyproj import Transformer

from .theme import LEVEL_COLOR, OCHRE, OXIDE, PAPER

DEMO_DIR = Path(__file__).resolve().parents[2] / "data" / "demo"

INDEX_RAMP = LinearSegmentedColormap.from_list("tv_index", [PAPER, OCHRE, OXIDE, "#4A1F10"])
SCORE_RAMP = LinearSegmentedColormap.from_list("tv_score", ["#F4F1EA", "#E3B98A", OXIDE, "#4A1F10"])
RAMPS = {"score": SCORE_RAMP, "index": INDEX_RAMP, "relief": colormaps["gray"]}


def list_demos() -> dict[str, Path]:
    out: dict[str, Path] = {}
    if DEMO_DIR.exists():
        for d in sorted(DEMO_DIR.iterdir()):
            if (d / "run.json").exists():
                meta = (
                    json.loads((d / "meta.json").read_text(encoding="utf-8"))
                    if (d / "meta.json").exists()
                    else {}
                )
                out[meta.get("title", d.name)] = d
    return out


def load_run(folder: Path) -> dict[str, Any]:
    run = json.loads((folder / "run.json").read_text(encoding="utf-8"))
    meta = folder / "meta.json"
    run["meta"] = json.loads(meta.read_text(encoding="utf-8")) if meta.exists() else {}
    return run


def load_zones(folder: Path, target: str) -> dict[str, Any]:
    return json.loads((folder / f"zones_{target}.geojson").read_text(encoding="utf-8"))


def _hex_to_rgba(h: str) -> tuple[float, float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)) + (1.0,)  # type: ignore[return-value]


def _bounds_wgs84(src: rasterio.DatasetReader) -> list[list[float]]:
    t = Transformer.from_crs(src.crs, 4326, always_xy=True)
    w, s, e, n = src.bounds
    lon0, lat0 = t.transform(w, s)
    lon1, lat1 = t.transform(e, n)
    return [[lat0, lon0], [lat1, lon1]]


def raster_overlay(
    folder: Path, name: str, kind: str, opacity: float
) -> tuple[str, list[list[float]]]:
    """PNG (data URI) + limites WGS84 para folium.ImageOverlay."""
    with rasterio.open(folder / f"{name}.tif") as src:
        arr = src.read(1).astype("float32")
        bounds = _bounds_wgs84(src)
    if kind == "class":
        rgba = np.zeros(arr.shape + (4,), dtype="float32")
        for code, level in ((0, "baixa"), (1, "media"), (2, "alta")):
            rgba[arr == code] = _hex_to_rgba(LEVEL_COLOR[level])
        # Baixa fica transparente: o mapa só destaca Média e Alta.
        rgba[..., 3] *= (arr >= 1) * (arr != 255) * opacity
    else:
        ok = np.isfinite(arr)
        lo, hi = np.nanpercentile(arr[ok], [2, 98]) if ok.any() else (0, 1)
        norm = np.clip((arr - lo) / max(hi - lo, 1e-9), 0, 1)
        rgba = RAMPS[kind](norm)
        rgba[..., 3] = np.where(ok, opacity, 0.0)
    img = Image.fromarray((rgba * 255).astype("uint8"), "RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), bounds
