"""Sentinel-2 L2A via STAC (Earth Search, AWS, acesso público sem credenciais)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import numpy as np

from .. import cache
from ..grid import Grid
from ..models import Unavailable
from . import _rio

STAC_URL = "https://earth-search.aws.element84.com/v1"
BANDS = ["blue", "red", "nir", "nir08", "swir16", "swir22"]
# SCL válido: 4 vegetação, 5 solo nu, 6 água, 7 não classificado (baixa prob.)
SCL_VALID = (4, 5, 6, 7)


@dataclass
class S2Composite:
    bands: dict[str, np.ndarray]  # reflectância 0–1, NaN onde inválido
    valid_fraction: float
    scene_ids: list[str]


def _default_dates(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    return date(today.year - 2, 1, 1), today


def fetch_sentinel2(
    grid: Grid,
    date_from: date | None = None,
    date_to: date | None = None,
    max_cloud_pct: float = 20.0,
    season_months: tuple[int, ...] = (5, 6, 7, 8, 9),
    max_scenes: int = 12,
) -> S2Composite | Unavailable:
    d0, d1 = _default_dates()
    date_from, date_to = date_from or d0, date_to or d1
    key = cache.make_key(
        "s2",
        epsg=grid.epsg,
        transform=tuple(grid.transform)[:6],
        shape=grid.shape,
        d0=date_from,
        d1=date_to,
        cloud=max_cloud_pct,
        months=season_months,
        n=max_scenes,
    )
    hit = cache.load(key)
    if hit:
        arrays, cached = hit
        return S2Composite(arrays, cached["valid_fraction"], cached["scene_ids"])

    try:
        import odc.stac
        from odc.geo.geobox import GeoBox
        from pystac_client import Client

        _rio.configure()
        bbox = grid.bbox_wgs84()
        items = list(
            Client.open(STAC_URL)
            .search(
                collections=["sentinel-2-l2a"],
                bbox=bbox,
                datetime=f"{date_from}/{date_to}",
                query={"eo:cloud_cover": {"lt": max_cloud_pct}},
            )
            .items()
        )
        items = [i for i in items if i.datetime and i.datetime.month in season_months]
        if not items:
            return Unavailable("sentinel2", "Sem cenas Sentinel-2 sem nuvens na época seca.")
        items.sort(key=lambda i: i.properties.get("eo:cloud_cover", 100))
        items = items[:max_scenes]

        geobox = GeoBox(grid.shape, grid.transform, grid.crs)
        ds = odc.stac.load(items, bands=[*BANDS, "scl"], geobox=geobox, chunks={}).compute()
    except Exception as exc:
        return Unavailable("sentinel2", f"Falha ao obter Sentinel-2: {exc}")

    good = ds["scl"].isin(SCL_VALID)
    bands: dict[str, np.ndarray] = {}
    for name in BANDS:
        # Reflectância L2A: DN/10000 (Earth Search já aplica offset nas propriedades raster).
        arr = ds[name].where(good & (ds[name] > 0)).astype("float32")
        bands[name] = np.asarray(arr.median("time", skipna=True).values, dtype=np.float32)
        if bands[name].max() > 10:  # DN bruto
            bands[name] = bands[name] / 10000.0
    valid = float(np.isfinite(bands["red"]).mean())
    ids = [i.id for i in items]
    meta: dict[str, Any] = {"valid_fraction": valid, "scene_ids": ids}
    cache.save(key, bands, meta)
    return S2Composite(bands, valid, ids)
