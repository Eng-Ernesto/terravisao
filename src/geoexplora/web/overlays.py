"""Camadas para o mapa (PNG + limites WGS 84) e acesso às pastas de dados.

Sem dependências de interface: usado pela API.
"""

from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from matplotlib import colormaps
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from pyproj import Transformer

PAPER, OCHRE, OXIDE, MOSS = "#F4F1EA", "#C9A227", "#B4532A", "#5E7A63"
LEVEL_COLOR = {"baixa": MOSS, "media": OCHRE, "alta": OXIDE}
INDEX_RAMP = LinearSegmentedColormap.from_list("gx_index", [PAPER, OCHRE, OXIDE, "#4A1F10"])
SCORE_RAMP = LinearSegmentedColormap.from_list("gx_score", [PAPER, "#E3B98A", OXIDE, "#4A1F10"])
RAMPS = {"score": SCORE_RAMP, "index": INDEX_RAMP, "relief": colormaps["gray"]}


def root() -> Path:
    """Raiz dos dados: variável GEOEXPLORA_ROOT, directório de trabalho ou o repositório."""
    env = os.environ.get("GEOEXPLORA_ROOT")
    if env:
        return Path(env)
    if (Path.cwd() / "data").exists():
        return Path.cwd()
    return Path(__file__).resolve().parents[3]


def demo_dir() -> Path:
    return root() / "data" / "demo"


def runs_dir() -> Path:
    return root() / "data" / "cache" / "runs"


def reference_dir() -> Path:
    return root() / "data" / "reference"


# ------------------------------------------------------------------------------- PNG
def png_uri(rgba: np.ndarray) -> str:
    img = Image.fromarray((np.clip(rgba, 0, 1) * 255).astype("uint8"), "RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _hex_rgba(h: str) -> tuple[float, float, float, float]:
    h = h.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return (r, g, b, 1.0)


def lonlat_bounds(x0: float, y0: float, x1: float, y1: float, epsg: int | str) -> list[list[float]]:
    """Caixa num CRS projectado → [[lat_sul, lon_oeste], [lat_norte, lon_este]]."""
    t = Transformer.from_crs(epsg, 4326, always_xy=True)
    lon0, lat0 = t.transform(x0, y0)
    lon1, lat1 = t.transform(x1, y1)
    return [[float(lat0), float(lon0)], [float(lat1), float(lon1)]]


def array_png(arr: np.ndarray, cmap: str, opacity: float = 0.85) -> str:
    """Matriz 2D → PNG transparente com rampa de cor (percentis 2–98)."""
    ok = np.isfinite(arr)
    if not ok.any():
        return png_uri(np.zeros(arr.shape + (4,)))
    lo, hi = np.nanpercentile(arr[ok], [2, 98])
    norm = np.clip((arr - lo) / max(float(hi - lo), 1e-9), 0, 1)
    rgba = colormaps[cmap](norm)
    rgba[..., 3] = np.where(ok, opacity, 0.0)
    return png_uri(rgba)


def raster_overlay(folder: Path, name: str, kind: str, opacity: float = 0.8) -> dict[str, Any]:
    """GeoTIFF de uma pasta de resultados → {png, bounds}. kind: class|score|index|relief|rgb."""
    with rasterio.open(folder / f"{name}.tif") as src:
        b = src.bounds
        bounds = lonlat_bounds(b.left, b.bottom, b.right, b.top, src.crs.to_string())
        if kind == "rgb":
            rgb = src.read([1, 2, 3]).astype("float32") / 255.0
            alpha = (rgb.sum(axis=0) > 0) * opacity
            return {"png": png_uri(np.dstack([np.moveaxis(rgb, 0, -1), alpha])), "bounds": bounds}
        arr = src.read(1).astype("float32")
    if kind == "class":
        rgba = np.zeros(arr.shape + (4,), dtype="float32")
        for code, level in ((1, "media"), (2, "alta")):  # baixa fica transparente
            rgba[arr == code] = _hex_rgba(LEVEL_COLOR[level])
        rgba[..., 3] *= (arr >= 1) * (arr != 255) * opacity
        return {"png": png_uri(rgba), "bounds": bounds}
    ok = np.isfinite(arr)
    lo, hi = np.nanpercentile(arr[ok], [2, 98]) if ok.any() else (0.0, 1.0)
    norm = np.clip((arr - lo) / max(float(hi - lo), 1e-9), 0, 1)
    rgba = RAMPS[kind](norm)
    rgba[..., 3] = np.where(ok, opacity, 0.0)
    return {"png": png_uri(rgba), "bounds": bounds}


# ------------------------------------------------------------------- resultados TerraVisão
def list_results() -> list[dict[str, Any]]:
    """Resultados do TerraVisão: exemplos incluídos e análises feitas (mais recentes primeiro)."""
    out: list[dict[str, Any]] = []
    for kind, base, newest_first in (("demo", demo_dir(), False), ("run", runs_dir(), True)):
        if not base.exists():
            continue
        for d in sorted(base.iterdir(), reverse=newest_first):
            if not (d / "run.json").exists():
                continue
            meta = _read_json(d / "meta.json")
            out.append(
                {
                    "id": f"{kind}:{d.name}",
                    "title": meta.get("title", d.name),
                    "region": meta.get("region", ""),
                    "kind": kind,
                    "has_rgb": (d / "layer_rgb.tif").exists(),
                }
            )
    return out


def result_folder(result_id: str) -> Path:
    kind, _, name = result_id.partition(":")
    base = {"demo": demo_dir(), "run": runs_dir()}.get(kind)
    if base is None or not name or "/" in name or "\\" in name or ".." in name:
        raise KeyError(result_id)
    folder = base / name
    if not (folder / "run.json").exists():
        raise KeyError(result_id)
    return folder


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def satellite_for(lon: np.ndarray, lat: np.ndarray, min_cover: float = 0.8) -> Path | None:
    """Resultado do TerraVisão com imagem RGB que cobre os pontos (contexto de satélite)."""
    for item in list_results():
        if not item["has_rgb"]:
            continue
        folder = result_folder(item["id"])
        with rasterio.open(folder / "layer_rgb.tif") as src:
            b = src.bounds
            (la0, lo0), (la1, lo1) = lonlat_bounds(
                b.left, b.bottom, b.right, b.top, src.crs.to_string()
            )
        inside = (lon >= lo0) & (lon <= lo1) & (lat >= la0) & (lat <= la1)
        if float(inside.mean()) >= min_cover:
            return folder
    return None
