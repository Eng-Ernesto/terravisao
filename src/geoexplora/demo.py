"""Conjuntos de demonstração (fictícios) em data/geoexplora/demo."""

from __future__ import annotations

import json
from pathlib import Path

from .loaders import GridLayer, Points, read_grid, read_points


def demo_dir() -> Path:
    """Pasta dos exemplos: relativa ao directório de trabalho (Docker) ou ao repositório."""
    here = Path("data/geoexplora/demo")
    return here if here.exists() else Path(__file__).resolve().parents[2] / here


def list_datasets() -> dict[str, Path]:
    base = demo_dir()
    out: dict[str, Path] = {}
    if base.exists():
        for d in sorted(base.iterdir()):
            if (d / "meta.json").exists() and (d / "amostras.csv").exists():
                meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
                out[meta.get("title", d.name)] = d
    return out


def load(folder: Path) -> tuple[Points, dict[str, GridLayer], dict[str, object]]:
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
    pts = read_points(folder / "amostras.csv", epsg=meta.get("epsg"))
    pts.title = meta.get("title", folder.name)
    pts.fictitious = bool(meta.get("fictitious", True))
    grids = {name: read_grid(folder / fn, name) for name, fn in meta.get("grids", {}).items()}
    return pts, grids, meta
