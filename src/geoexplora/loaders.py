"""Leitura dos dados do geofísico: pontos (CSV, GeoJSON, Shapefile zip) e grelhas (GeoTIFF)."""

from __future__ import annotations

import io
import json
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shapely
from affine import Affine
from pyproj import Transformer

from terravisao.aoi import angola_boundary, utm_epsg

DEFAULT_UTM = 32733  # WGS 84 / UTM 33S, o fuso de Longonjo
MIN_POINTS = 10

X_NAMES = ("x", "easting", "east", "lon", "long", "longitude", "x_utm", "x_teste")
Y_NAMES = ("y", "northing", "north", "lat", "latitude", "y_utm", "y_teste")
ID_NAMES = ("amostra", "id", "sample", "sample_id", "codigo", "código")
ELEMENT_COL = re.compile(r"^(?P<el>[A-Za-z]{1,2})_(?P<unit>ppm|ppb|pct)$", re.IGNORECASE)
UNIT_TO_PPM = {"ppm": 1.0, "ppb": 1e-3, "pct": 1e4}
RESERVED = {"id", "lon", "lat", "x", "y"}


class LoadError(ValueError):
    """Ficheiro inválido; a mensagem é mostrável ao utilizador."""


@dataclass
class Points:
    """Amostras georreferenciadas. `df` tem id, lon, lat, x, y (UTM) e os atributos numéricos."""

    df: pd.DataFrame
    epsg: int  # UTM de trabalho (colunas x, y)
    elements: list[str]  # elementos de terras raras presentes, ex. ["Ce", "La"]
    covariates: list[str]  # outras colunas numéricas (geofísica, etc.)
    source: str = ""
    title: str = ""
    fictitious: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass
class GridLayer:
    """Grelha raster (um canal) em CRS projectado, com NaN onde não há dados."""

    name: str
    array: np.ndarray
    transform: Affine
    epsg: int

    @property
    def resolution(self) -> float:
        return float(abs(self.transform.a))

    def bounds(self) -> tuple[float, float, float, float]:
        rows, cols = self.array.shape
        x0, y1 = self.transform.c, self.transform.f
        return x0, y1 + rows * self.transform.e, x0 + cols * self.transform.a, y1


def _pick(columns: list[str], names: tuple[str, ...]) -> str | None:
    lower = {c.lower(): c for c in columns}
    for n in names:
        if n in lower:
            return lower[n]
    return None


def _decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise LoadError("Não foi possível ler o ficheiro como texto.")


def _fix_decimal_commas(table: pd.DataFrame) -> pd.DataFrame:
    """Colunas em texto como «527,5» (Excel em português) passam a números.

    Só converte uma coluna se pelo menos 80 % dos valores forem numéricos depois da troca,
    para não estragar colunas de identificadores.
    """
    table = table.copy()
    for c in table.columns:
        if not pd.api.types.is_numeric_dtype(table[c]):  # texto (object ou StringDtype)
            fixed = pd.to_numeric(
                table[c].astype(str).str.strip().str.replace(",", ".", regex=False),
                errors="coerce",
            )
            if fixed.notna().mean() >= 0.8:
                table[c] = fixed
    return table


def _build(
    table: pd.DataFrame,
    x_col: str | None,
    y_col: str | None,
    epsg: int | None,
    source: str,
) -> Points:
    table = _fix_decimal_commas(table)
    cols = list(table.columns)
    x_col = x_col or _pick(cols, X_NAMES)
    y_col = y_col or _pick(cols, Y_NAMES)
    if not x_col or not y_col:
        raise LoadError(
            "Não encontrei as colunas de coordenadas. Use nomes como X e Y (UTM) ou lon e lat."
        )
    id_col = _pick(cols, ID_NAMES)
    warns: list[str] = []

    out = pd.DataFrame(
        {
            "id": table[id_col].astype(str)
            if id_col
            else [f"P{i + 1:03d}" for i in range(len(table))],
            "_x": pd.to_numeric(table[x_col], errors="coerce"),
            "_y": pd.to_numeric(table[y_col], errors="coerce"),
        }
    )
    elements: list[str] = []
    covariates: list[str] = []
    for c in cols:
        if c in (x_col, y_col, id_col):
            continue
        values = pd.to_numeric(table[c], errors="coerce")
        if values.notna().sum() < max(3, 0.5 * len(table)):
            continue  # coluna de texto ou quase vazia
        m = ELEMENT_COL.match(c)
        if m:
            el = m.group("el").capitalize()
            out[f"{el}_ppm"] = values * UNIT_TO_PPM[m.group("unit").lower()]
            elements.append(el)
        else:
            out[c] = values
            covariates.append(c)

    n0 = len(out)
    out = out.dropna(subset=["_x", "_y"]).reset_index(drop=True)
    if len(out) < n0:
        warns.append(f"{n0 - len(out)} linhas sem coordenadas válidas foram ignoradas.")
    if len(out) < MIN_POINTS:
        raise LoadError(f"São precisas pelo menos {MIN_POINTS} amostras com coordenadas.")

    geographic = out["_x"].abs().max() <= 180 and out["_y"].abs().max() <= 90
    if geographic:
        lon, lat = out["_x"].to_numpy(), out["_y"].to_numpy()
    else:
        t = Transformer.from_crs(epsg or DEFAULT_UTM, 4326, always_xy=True)
        lon, lat = t.transform(out["_x"].to_numpy(), out["_y"].to_numpy())
        if epsg is None:
            warns.append(f"Coordenadas lidas como UTM (EPSG:{DEFAULT_UTM}, WGS 84 / UTM 33S).")
    out["lon"], out["lat"] = lon, lat
    work_epsg = utm_epsg(float(np.median(lon)), float(np.median(lat)))
    tx = Transformer.from_crs(4326, work_epsg, always_xy=True)
    out["x"], out["y"] = tx.transform(lon, lat)
    out = out.drop(columns=["_x", "_y"])
    ordered = ["id", "lon", "lat", "x", "y"] + [c for c in out.columns if c not in RESERVED]
    out = out[ordered]

    boundary = angola_boundary()
    if boundary is not None:
        inside = shapely.contains_xy(boundary, out["lon"].to_numpy(), out["lat"].to_numpy())
        if not inside.all():
            warns.append(
                f"{int((~inside).sum())} de {len(out)} amostras caem fora de Angola. "
                "Verifique o sistema de coordenadas."
            )
    return Points(out, work_epsg, elements, covariates, source=source, warnings=warns)


def read_points(
    data: bytes | str | Path,
    filename: str = "",
    epsg: int | None = None,
    x_col: str | None = None,
    y_col: str | None = None,
) -> Points:
    """Lê pontos de CSV, GeoJSON ou Shapefile (.zip). `epsg` aplica-se a coordenadas projectadas."""
    if isinstance(data, (str, Path)):
        filename = filename or str(data)
        data = Path(data).read_bytes()
    name = filename.lower()
    try:
        if name.endswith((".geojson", ".json")):
            return _build(_geojson_table(json.loads(_decode(data))), "lon", "lat", None, filename)
        if name.endswith(".zip"):
            return _build(_shapefile_table(data), "lon", "lat", None, filename)
        text = _decode(data)
        # O separador decide-se pelo cabeçalho: os valores podem ter vírgulas decimais.
        header = text.lstrip("﻿").splitlines()[0] if text.strip() else ""
        sep = ";" if ";" in header and "," not in header else "\t" if "\t" in header else None
        table = pd.read_csv(io.StringIO(text), sep=sep, engine="python")
    except LoadError:
        raise
    except Exception as exc:
        raise LoadError(f"Não foi possível ler «{filename or 'ficheiro'}»: {exc}") from exc
    return _build(table, x_col, y_col, epsg, filename)


def _geojson_table(gj: dict[str, Any]) -> pd.DataFrame:
    feats = gj["features"] if gj.get("type") == "FeatureCollection" else [gj]
    rows = []
    for f in feats:
        g = f.get("geometry") or {}
        if g.get("type") != "Point":
            continue
        lon, lat = g["coordinates"][:2]
        rows.append({**(f.get("properties") or {}), "lon": lon, "lat": lat})
    if not rows:
        raise LoadError("O GeoJSON não tem pontos (geometrias do tipo Point).")
    return pd.DataFrame(rows)


def _shapefile_table(raw: bytes) -> pd.DataFrame:
    import geopandas as gpd

    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "dados.zip"
        zpath.write_bytes(raw)
        gdf = gpd.read_file(f"zip://{zpath}")
    gdf = gdf[gdf.geometry.geom_type == "Point"].to_crs(4326)
    if gdf.empty:
        raise LoadError("O Shapefile não tem pontos.")
    table = pd.DataFrame(gdf.drop(columns="geometry"))
    table["lon"], table["lat"] = gdf.geometry.x.to_numpy(), gdf.geometry.y.to_numpy()
    return table


# ----------------------------------------------------------------------------- grelhas
def read_grid(data: bytes | str | Path, name: str = "grelha") -> GridLayer:
    """Lê um GeoTIFF (canal 1). Se estiver em graus, reprojecta para o UTM da área."""
    import rasterio
    from rasterio.io import MemoryFile
    from rasterio.warp import Resampling, calculate_default_transform, reproject

    def _open(src: Any) -> GridLayer:
        arr = src.read(1).astype("float32")
        if src.nodata is not None:
            arr[arr == src.nodata] = np.nan
        if src.crs is None:
            raise LoadError("O GeoTIFF não tem sistema de coordenadas.")
        if src.crs.is_projected:
            return GridLayer(name, arr, src.transform, int(src.crs.to_epsg() or DEFAULT_UTM))
        cx, cy = (src.bounds.left + src.bounds.right) / 2, (src.bounds.top + src.bounds.bottom) / 2
        epsg = utm_epsg(cx, cy)
        tr, w, h = calculate_default_transform(
            src.crs, f"EPSG:{epsg}", src.width, src.height, *src.bounds
        )
        dst = np.full((h, w), np.nan, dtype="float32")
        reproject(
            arr,
            dst,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=tr,
            dst_crs=f"EPSG:{epsg}",
            resampling=Resampling.bilinear,
            dst_nodata=np.nan,
        )
        return GridLayer(name, dst, tr, epsg)

    try:
        if isinstance(data, (str, Path)):
            with rasterio.open(data) as src:
                return _open(src)
        with MemoryFile(data) as mem, mem.open() as src:
            return _open(src)
    except LoadError:
        raise
    except Exception as exc:
        raise LoadError(f"Não foi possível ler o GeoTIFF: {exc}") from exc


def sample_grid(layer: GridLayer, lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Valor da grelha em cada ponto (NaN fora da grelha)."""
    t = Transformer.from_crs(4326, layer.epsg, always_xy=True)
    x, y = t.transform(lon, lat)
    inv = ~layer.transform
    col, row = inv @ (np.asarray(x), np.asarray(y))
    r, c = np.floor(row).astype(int), np.floor(col).astype(int)
    ok = (r >= 0) & (r < layer.array.shape[0]) & (c >= 0) & (c < layer.array.shape[1])
    out = np.full(len(r), np.nan, dtype="float64")
    out[ok] = layer.array[r[ok], c[ok]]
    return out
