"""Mapas estáticos para o relatório (matplotlib, sem rede).

Lêem a pasta de exportação (GeoTIFF + GeoJSON + run.json). O fundo é o relevo sombreado.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import shapely
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from pyproj import Transformer
from shapely.geometry import shape

INK = "#1C1B18"
INK_SOFT = "#6B675D"
OXIDE = "#B4532A"
OCHRE = "#C9A227"
MOSS = "#5E7A63"
PAPER = "#F4F1EA"

RAMP = LinearSegmentedColormap.from_list("tv", [PAPER, OCHRE, OXIDE, "#4A1F10"])
SCORE = LinearSegmentedColormap.from_list("tv_score", [PAPER, "#E3B98A", OXIDE, "#4A1F10"])


def _read(
    folder: Path, name: str
) -> tuple[np.ndarray, tuple[float, float, float, float], Any] | None:
    path = folder / f"{name}.tif"
    if not path.exists():
        return None
    with rasterio.open(path) as src:
        b = src.bounds
        return src.read(1).astype("float32"), (b.left, b.right, b.bottom, b.top), src.crs


def _to_crs(geom: Any, crs: Any) -> Any:
    t = Transformer.from_crs(4326, crs, always_xy=True)

    def project(coords: np.ndarray) -> np.ndarray:
        x, y = t.transform(coords[:, 0], coords[:, 1])
        return np.column_stack([x, y])

    return shapely.transform(geom, project)


def _polys(geom: Any) -> list[Any]:
    return list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]


def _png(fig: Any) -> bytes:
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="jpeg",
        dpi=125,
        bbox_inches="tight",
        facecolor="white",
        pil_kwargs={"quality": 88, "optimize": True},
    )
    plt.close(fig)
    return buf.getvalue()


def _scalebar(ax: Any, extent: tuple[float, float, float, float]) -> None:
    left, right, bottom, top = extent
    width = right - left
    length = max(n for n in (100, 200, 500, 1000, 2000, 5000, 10000) if n <= width / 3 or n == 100)
    x0, y0 = left + width * 0.04, bottom + (top - bottom) * 0.05
    ax.plot([x0, x0 + length], [y0, y0], color=INK, lw=2.5, solid_capstyle="butt")
    label = f"{length // 1000} km" if length >= 1000 else f"{length} m"
    ax.text(x0, y0 + (top - bottom) * 0.015, label, fontsize=7, color=INK, va="bottom")


def _base(folder: Path, title: str) -> tuple[Any, Any, tuple[float, float, float, float], Any]:
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    hs = _read(folder, "layer_hillshade")
    ref = (
        hs
        or _read(folder, "class_ferro")
        or next(
            (r for p in sorted(folder.glob("class_*.tif")) if (r := _read(folder, p.stem))), None
        )
    )
    if ref is None:
        raise FileNotFoundError("Sem rasters na pasta de resultados.")
    arr, extent, crs = ref
    if hs:
        ax.imshow(arr, extent=extent, cmap="gray", vmin=0, vmax=1, alpha=0.55, zorder=0)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#D8D2C4")
    ax.set_title(title, fontsize=11, color=INK, loc="left", pad=8)
    return fig, ax, extent, crs


def _aoi_outline(ax: Any, folder: Path, crs: Any) -> None:
    run = json.loads((folder / "run.json").read_text(encoding="utf-8"))
    geom = _to_crs(shape(run["request"]["geometry"]), crs)
    for p in _polys(geom):
        x, y = p.exterior.xy
        ax.plot(x, y, color=INK, lw=1, ls=(0, (4, 3)), zorder=5)


def class_map(folder: Path, target: str, title: str) -> bytes:
    fig, ax, extent, crs = _base(folder, title)
    cls = _read(folder, f"class_{target}")
    if cls is not None:
        arr = cls[0]
        rgba = np.zeros(arr.shape + (4,), dtype="float32")
        for code, color in ((1, OCHRE), (2, OXIDE)):
            rgba[arr == code] = matplotlib.colors.to_rgba(color, 0.8)
        ax.imshow(rgba, extent=extent, zorder=2, interpolation="nearest")
    zpath = folder / f"zones_{target}.geojson"
    if zpath.exists():
        for feat in json.loads(zpath.read_text(encoding="utf-8"))["features"]:
            geom = _to_crs(shape(feat["geometry"]), crs)
            for p in _polys(geom):
                x, y = p.exterior.xy
                ax.plot(x, y, color=INK, lw=1.4, zorder=6)
            pt = max(_polys(geom), key=lambda g: g.area).representative_point()
            ax.annotate(
                feat["properties"]["id"],
                (pt.x, pt.y),
                fontsize=9,
                fontweight="bold",
                color="white",
                ha="center",
                va="center",
                zorder=7,
                bbox={"boxstyle": "circle,pad=0.2", "fc": INK, "ec": "none"},
            )
    _aoi_outline(ax, folder, crs)
    _scalebar(ax, extent)
    ax.legend(
        handles=[
            Patch(fc=OCHRE, alpha=0.8, label="Probabilidade média"),
            Patch(fc=OXIDE, alpha=0.8, label="Probabilidade alta"),
        ],
        loc="upper right",
        fontsize=7,
        frameon=True,
        framealpha=0.9,
        edgecolor="#D8D2C4",
    )
    return _png(fig)


def layer_map(folder: Path, name: str, title: str, kind: str = "index") -> bytes | None:
    data = _read(folder, name)
    if data is None:
        return None
    fig, ax, extent, crs = _base(folder, title)
    arr = data[0]
    ok = np.isfinite(arr)
    if not ok.any():
        plt.close(fig)
        return None
    lo, hi = np.nanpercentile(arr[ok], [2, 98])
    cmap = {"index": RAMP, "score": SCORE, "slope": RAMP}.get(kind, RAMP)
    im = ax.imshow(
        np.where(ok, arr, np.nan), extent=extent, cmap=cmap, vmin=lo, vmax=hi, alpha=0.85, zorder=2
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.ax.tick_params(labelsize=7, colors=INK_SOFT)
    cbar.outline.set_edgecolor("#D8D2C4")
    _aoi_outline(ax, folder, crs)
    _scalebar(ax, extent)
    return _png(fig)
