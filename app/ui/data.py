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

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "data" / "demo"
REFERENCE_DIR = ROOT / "data" / "reference"
RUNS_DIR = ROOT / "data" / "cache" / "runs"  # análises feitas na app

INDEX_RAMP = LinearSegmentedColormap.from_list("tv_index", [PAPER, OCHRE, OXIDE, "#4A1F10"])
SCORE_RAMP = LinearSegmentedColormap.from_list("tv_score", ["#F4F1EA", "#E3B98A", OXIDE, "#4A1F10"])
RAMPS = {"score": SCORE_RAMP, "index": INDEX_RAMP, "relief": colormaps["gray"]}


def list_demos() -> dict[str, Path]:
    """Demonstrações incluídas e análises feitas na app (as mais recentes primeiro)."""
    out: dict[str, Path] = {}
    for base, newest_first in ((DEMO_DIR, False), (RUNS_DIR, True)):
        if not base.exists():
            continue
        for d in sorted(base.iterdir(), reverse=newest_first):
            if (d / "run.json").exists():
                meta_file = d / "meta.json"
                meta = (
                    json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}
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
        bounds = _bounds_wgs84(src)
        if kind == "rgb":
            rgb = src.read([1, 2, 3]).astype("float32") / 255.0
            alpha = (rgb.sum(axis=0) > 0) * opacity
            rgba = np.dstack([np.moveaxis(rgb, 0, -1), alpha])
            return _png_uri(rgba), bounds
        arr = src.read(1).astype("float32")
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
    return _png_uri(rgba), bounds


def _png_uri(rgba: np.ndarray) -> str:
    img = Image.fromarray((rgba * 255).astype("uint8"), "RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def has_layer(folder: Path, name: str) -> bool:
    return (folder / f"{name}.tif").exists()


def provinces() -> dict[str, Any]:
    """Províncias de Angola (geoBoundaries, domínio público): base cartográfica offline."""
    return json.loads((REFERENCE_DIR / "angola_provincias.geojson").read_text(encoding="utf-8"))


_ONLINE_CACHE: dict[str, float] = {}


def is_online(host: str = "server.arcgisonline.com", ttl: float = 60.0) -> bool:
    """Há internet? Teste rápido de ligação, guardado durante `ttl` segundos."""
    import socket
    import time

    now = time.time()
    if "t" in _ONLINE_CACHE and now - _ONLINE_CACHE["t"] < ttl:
        return bool(_ONLINE_CACHE["ok"])
    try:
        socket.create_connection((host, 443), timeout=1.5).close()
        ok = 1.0
    except OSError:
        ok = 0.0
    _ONLINE_CACHE.update(t=now, ok=ok)
    return bool(ok)


def lonlat_bounds(x0: float, y0: float, x1: float, y1: float, epsg: int) -> list[list[float]]:
    """Limites de uma caixa em UTM como [[lat0, lon0], [lat1, lon1]] para o folium."""
    t = Transformer.from_crs(epsg, 4326, always_xy=True)
    lon0, lat0 = t.transform(x0, y0)
    lon1, lat1 = t.transform(x1, y1)
    return [[lat0, lon0], [lat1, lon1]]


def array_png(arr: np.ndarray, cmap: str, vmin: float, vmax: float, opacity: float) -> str:
    """Matriz 2D -> PNG transparente (data URI) com a rampa de cor escolhida."""
    ok = np.isfinite(arr)
    norm = np.clip((arr - vmin) / max(vmax - vmin, 1e-9), 0, 1)
    rgba = colormaps[cmap](norm)
    rgba[..., 3] = np.where(ok, opacity, 0.0)
    return _png_uri(rgba)


def find_satellite_base(lon: np.ndarray, lat: np.ndarray, min_cover: float = 0.8) -> Path | None:
    """Resultado do TerraVisão com imagem RGB que cobre as amostras (contexto de satélite)."""
    for folder in list_demos().values():
        tif = folder / "layer_rgb.tif"
        if not tif.exists():
            continue
        with rasterio.open(tif) as src:
            (la0, lo0), (la1, lo1) = _bounds_wgs84(src)
        inside = (lon >= lo0) & (lon <= lo1) & (lat >= la0) & (lat <= la1)
        if float(inside.mean()) >= min_cover:
            return folder
    return None
