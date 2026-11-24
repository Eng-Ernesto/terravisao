"""Geologia: shapefile local (p.ex. BGS Africa Groundwater Atlas, 1:5M) -> favorabilidade por alvo.

O ficheiro não vem no repositório (licença por confirmar, docs/04). Colocar em
`data/reference/geologia/` (um .shp). Sem ficheiro, devolve `Unavailable` e o pipeline segue.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..config import Target
from ..grid import Grid
from ..models import Unavailable

GEOLOGY_DIR = Path("data/reference/geologia")
RULES_CSV = Path("data/reference/litologia_regras.csv")


def load_rules(path: Path = RULES_CSV) -> dict[str, dict[str, float]]:
    """CSV: unidade + uma coluna por alvo (valores 0–1). Chave = texto da unidade."""
    import csv

    rules: dict[str, dict[str, float]] = {}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(line for line in fh if not line.startswith("#")):
            rules[row["unidade"].strip().lower()] = {t.value: float(row[t.value]) for t in Target}
    return rules


def lithology_favorability(
    grid: Grid,
    target: Target,
    column: str,
    geology_dir: Path = GEOLOGY_DIR,
    rules_path: Path = RULES_CSV,
) -> np.ndarray | Unavailable:
    shp = next(iter(sorted(geology_dir.glob("*.shp"))), None) if geology_dir.exists() else None
    if shp is None:
        return Unavailable("geology", "Sem ficheiro de geologia em data/reference/geologia/.")
    if not rules_path.exists():
        return Unavailable("geology", "Sem tabela de regras de litologia.")
    try:
        import geopandas as gpd
        from rasterio.features import rasterize

        gdf = gpd.read_file(shp).to_crs(grid.epsg)
        rules = load_rules(rules_path)
        shapes = []
        for geom, unit in zip(gdf.geometry, gdf[column].astype(str), strict=True):
            value = rules.get(unit.strip().lower(), {}).get(target.value)
            if value is not None:
                shapes.append((geom, float(value)))
        if not shapes:
            return Unavailable("geology", "Nenhuma unidade geológica coincide com as regras.")
        arr = rasterize(
            shapes, out_shape=grid.shape, transform=grid.transform, fill=np.nan, dtype="float32"
        )
    except Exception as exc:
        return Unavailable("geology", f"Falha ao ler geologia: {exc}")
    return np.asarray(arr, dtype=np.float32)
