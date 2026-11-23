"""Grelha comum (CRS UTM + transform + shape) partilhada por todas as camadas."""

from __future__ import annotations

import math
from dataclasses import dataclass

from affine import Affine
from pyproj import Transformer
from shapely.geometry.base import BaseGeometry

from .aoi import utm_epsg


@dataclass(frozen=True)
class Grid:
    epsg: int
    transform: Affine
    shape: tuple[int, int]  # (linhas, colunas)

    @property
    def crs(self) -> str:
        return f"EPSG:{self.epsg}"

    @property
    def resolution(self) -> float:
        return float(self.transform.a)

    @property
    def pixel_area_km2(self) -> float:
        return (self.resolution**2) / 1e6

    def bbox_wgs84(self) -> tuple[float, float, float, float]:
        rows, cols = self.shape
        t = Transformer.from_crs(self.epsg, 4326, always_xy=True)
        xs = [self.transform.c, self.transform.c + cols * self.transform.a]
        ys = [self.transform.f, self.transform.f + rows * self.transform.e]
        lons, lats = t.transform([xs[0], xs[1], xs[0], xs[1]], [ys[0], ys[0], ys[1], ys[1]])
        return (min(lons), min(lats), max(lons), max(lats))

    @classmethod
    def from_aoi(cls, geom: BaseGeometry, resolution: float, buffer_m: float = 0.0) -> Grid:
        """Grelha que cobre a AOI (mais margem), alinhada a múltiplos da resolução."""
        c = geom.centroid
        epsg = utm_epsg(c.x, c.y)
        t = Transformer.from_crs(4326, epsg, always_xy=True)
        minx, miny, maxx, maxy = geom.bounds
        xs, ys = t.transform([minx, maxx, minx, maxx], [miny, miny, maxy, maxy])
        x0 = math.floor((min(xs) - buffer_m) / resolution) * resolution
        x1 = math.ceil((max(xs) + buffer_m) / resolution) * resolution
        y0 = math.floor((min(ys) - buffer_m) / resolution) * resolution
        y1 = math.ceil((max(ys) + buffer_m) / resolution) * resolution
        cols = int(round((x1 - x0) / resolution))
        rows = int(round((y1 - y0) / resolution))
        return cls(epsg, Affine(resolution, 0, x0, 0, -resolution, y1), (rows, cols))

    def mask_of(self, geom: BaseGeometry) -> object:
        """Máscara booleana (True dentro da AOI) na grelha."""
        import numpy as np
        import shapely
        from pyproj import Transformer as T
        from rasterio.features import rasterize

        t = T.from_crs(4326, self.epsg, always_xy=True)

        def project(coords: np.ndarray) -> np.ndarray:
            x, y = t.transform(coords[:, 0], coords[:, 1])
            return np.column_stack([x, y])

        utm_geom = shapely.transform(geom, project)
        return rasterize(
            [(utm_geom, 1)], out_shape=self.shape, transform=self.transform, fill=0, dtype="uint8"
        ).astype(bool)
