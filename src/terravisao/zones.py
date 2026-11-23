"""Extracção de zonas prioritárias (docs/05 §8)."""

from __future__ import annotations

import string

import numpy as np
from scipy import ndimage

from .config import Target
from .models import Zone

LABELS = list(string.ascii_uppercase)


def extract_zones(
    classes: np.ndarray,
    score: np.ndarray,
    layers: dict[str, np.ndarray],
    weights: dict[str, float],
    target: Target,
    pixel_area_km2: float,
    min_area_km2: float,
    recommendation: str = "",
    min_class: int = 2,
) -> tuple[list[Zone], np.ndarray]:
    """Devolve zonas ordenadas (A, B, C…) e o raster de rótulos (0 = fora de zona)."""
    mask = classes != 255
    mask &= classes >= min_class
    mask = ndimage.binary_opening(mask, iterations=1)  # remove ruído de 1 pixel
    mask = ndimage.binary_closing(mask, iterations=1)
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    zones: list[Zone] = []
    for i in range(1, n + 1):
        sel = lab == i
        area = float(sel.sum() * pixel_area_km2)
        if area < min_area_km2:
            continue
        contrib = {
            name: float(np.nanmean(layers[name][sel]) * w)
            for name, w in weights.items()
            if name in layers and np.isfinite(layers[name][sel]).any()
        }
        zones.append(
            Zone(
                id=str(i),
                target=target,
                area_km2=area,
                mean_score=float(np.nanmean(score[sel])),
                max_score=float(np.nanmax(score[sel])),
                contributions=contrib,
                recommendation=recommendation,
            )
        )
    zones.sort(key=lambda z: z.mean_score * z.area_km2, reverse=True)
    relabel = np.zeros_like(lab)
    for rank, z in enumerate(zones):
        relabel[lab == int(z.id)] = rank + 1
        z.id = LABELS[rank] if rank < len(LABELS) else str(rank + 1)
    return zones, relabel
