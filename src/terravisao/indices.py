"""Índices espectrais (docs/05 §2). Funções puras sobre arrays de reflectância."""

from __future__ import annotations

import numpy as np


def _ratio(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    out = np.full(a.shape, np.nan, dtype=np.float32)
    np.divide(a, b, out=out, where=(b != 0) & np.isfinite(a) & np.isfinite(b))
    return out


def iron_oxide(red: np.ndarray, blue: np.ndarray) -> np.ndarray:
    """Óxido de ferro (férrico): B04/B02."""
    return _ratio(red, blue)


def ferrous(swir1: np.ndarray, nir_narrow: np.ndarray) -> np.ndarray:
    """Ferroso: B11/B8A."""
    return _ratio(swir1, nir_narrow)


def clay(swir1: np.ndarray, swir2: np.ndarray) -> np.ndarray:
    """Alteração argilosa / hidroxilos: B11/B12."""
    return _ratio(swir1, swir2)


def _normalized_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a.astype(np.float32)
    b = b.astype(np.float32)
    s = a + b
    out = np.full(a.shape, np.nan, dtype=np.float32)
    np.divide(a - b, s, out=out, where=(s != 0) & np.isfinite(s))
    return out


def ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    return _normalized_difference(nir, red)


def ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    return _normalized_difference(green, nir)
