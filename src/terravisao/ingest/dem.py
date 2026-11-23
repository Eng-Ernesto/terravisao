"""Modelo digital de elevação.

Usa Copernicus DEM GLO-30 (Earth Search, AWS, aberto e sem credenciais), equivalente em
resolução (~30 m) ao SRTM. Decisão: ADR-13 em docs/10.
"""

from __future__ import annotations

import numpy as np

from .. import cache
from ..grid import Grid
from ..models import Unavailable
from . import _rio
from .sentinel2 import STAC_URL


def fetch_dem(grid: Grid) -> np.ndarray | Unavailable:
    key = cache.make_key(
        "dem", epsg=grid.epsg, transform=tuple(grid.transform)[:6], shape=grid.shape
    )
    hit = cache.load(key)
    if hit:
        return hit[0]["z"]
    try:
        import odc.stac
        from odc.geo.geobox import GeoBox
        from pystac_client import Client

        _rio.configure()
        items = list(
            Client.open(STAC_URL)
            .search(collections=["cop-dem-glo-30"], bbox=grid.bbox_wgs84())
            .items()
        )
        if not items:
            return Unavailable("dem", "Sem tiles de DEM para a área.")
        geobox = GeoBox(grid.shape, grid.transform, grid.crs)
        ds = odc.stac.load(items, geobox=geobox, resampling="bilinear", chunks={}).compute()
        z = np.asarray(ds["data"].isel(time=0).values, dtype=np.float32)
    except Exception as exc:
        return Unavailable("dem", f"Falha ao obter DEM: {exc}")
    z[z < -500] = np.nan  # valores de vazio
    cache.save(key, {"z": z}, {"source": "cop-dem-glo-30"})
    return z
