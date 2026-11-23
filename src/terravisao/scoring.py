"""Normalização, pontuação ponderada e classificação (docs/05 §5–7)."""

from __future__ import annotations

import numpy as np

from .config import SETTINGS, Level


def normalize(
    array: np.ndarray,
    percentiles: tuple[float, float] | None = None,
    invert: bool = False,
) -> np.ndarray:
    """Escala para 0–1 pelos percentis da própria área. NaN é preservado."""
    lo_p, hi_p = percentiles or SETTINGS.percentiles
    valid = array[np.isfinite(array)]
    if valid.size == 0:
        return np.full(array.shape, np.nan, dtype=np.float32)
    lo, hi = np.percentile(valid, [lo_p, hi_p])
    if hi <= lo:
        out = np.full(array.shape, 0.5, dtype=np.float32)
        out[~np.isfinite(array)] = np.nan
    else:
        out = np.clip((array - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)
    return (1.0 - out) if invert else out


def weighted_score(layers: dict[str, np.ndarray], weights: dict[str, float]) -> np.ndarray:
    """Soma ponderada só sobre camadas disponíveis, com pesos renormalizados.

    Camadas ausentes em `layers` são ignoradas; o chamador deve avisar o utilizador.
    """
    available = {k: w for k, w in weights.items() if k in layers and w > 0}
    if not available:
        raise ValueError("Nenhuma camada disponível para calcular a pontuação.")
    total = sum(available.values())
    shape = next(iter(layers.values())).shape
    acc = np.zeros(shape, dtype=np.float32)
    wsum = np.zeros(shape, dtype=np.float32)
    for name, w in available.items():
        layer = layers[name]
        ok = np.isfinite(layer)
        acc += np.where(ok, layer, 0.0) * (w / total)
        wsum += np.where(ok, w / total, 0.0)
    out = np.full(shape, np.nan, dtype=np.float32)
    np.divide(acc, wsum, out=out, where=wsum > 0)
    return out


def smooth(score: np.ndarray, sigma_px: float) -> np.ndarray:
    """Suavização gaussiana que ignora NaN (convolução normalizada).

    Agrega a pontuação em manchas contínuas, evitando zonas fragmentadas por ruído de pixel.
    """
    if sigma_px <= 0:
        return score
    from scipy import ndimage

    ok = np.isfinite(score)
    num = ndimage.gaussian_filter(np.where(ok, score, 0.0).astype(np.float32), sigma_px)
    den = ndimage.gaussian_filter(ok.astype(np.float32), sigma_px)
    out = np.full(score.shape, np.nan, dtype=np.float32)
    np.divide(num, den, out=out, where=(den > 1e-3) & ok)
    return out


def classify(
    score: np.ndarray,
    threshold_medium: float | None = None,
    threshold_high: float | None = None,
) -> np.ndarray:
    """0 = baixa, 1 = média, 2 = alta; 255 onde a pontuação é inválida."""
    t_med = SETTINGS.threshold_medium if threshold_medium is None else threshold_medium
    t_high = SETTINGS.threshold_high if threshold_high is None else threshold_high
    out = np.full(score.shape, 255, dtype=np.uint8)
    ok = np.isfinite(score)
    out[ok] = 0
    out[ok & (score >= t_med)] = 1
    out[ok & (score >= t_high)] = 2
    return out


def level_name(code: int) -> Level:
    return {0: Level.LOW, 1: Level.MEDIUM, 2: Level.HIGH}[code]
