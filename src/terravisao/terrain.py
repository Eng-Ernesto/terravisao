"""Derivadas de terreno a partir do DEM (docs/05 §3). Funções puras sobre arrays 2D."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np
from scipy import ndimage
from skimage import feature, transform
from skimage.draw import line as draw_line

# Vizinhança D8: (dr, dc, distância relativa)
_D8 = [
    (-1, -1, 2**0.5),
    (-1, 0, 1.0),
    (-1, 1, 2**0.5),
    (0, -1, 1.0),
    (0, 1, 1.0),
    (1, -1, 2**0.5),
    (1, 0, 1.0),
    (1, 1, 2**0.5),
]


def slope_deg(z: np.ndarray, res: float) -> np.ndarray:
    gy, gx = np.gradient(z.astype(np.float32), res)
    return np.degrees(np.arctan(np.hypot(gx, gy))).astype(np.float32)


def hillshade(
    z: np.ndarray, res: float, azimuth: float = 315.0, altitude: float = 45.0
) -> np.ndarray:
    """Hillshade 0–1 (azimute em graus a partir do Norte, sentido horário)."""
    gy, gx = np.gradient(z.astype(np.float32), res)
    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(gx, -gy)  # direcção de descida, a partir do Norte
    az, alt = np.radians(azimuth), np.radians(altitude)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect + np.pi)
    return np.clip(hs, 0.0, 1.0).astype(np.float32)


def fill_depressions(z: np.ndarray, eps: float = 1e-3) -> np.ndarray:
    """Priority-flood com epsilon (Barnes 2014): cada pixel interior fica com vizinho mais baixo."""
    z = np.nan_to_num(z, nan=float(np.nanmin(z))).astype(np.float64)
    rows, cols = z.shape
    out = z.copy()
    closed = np.zeros_like(z, dtype=bool)
    heap: list[tuple[float, int, int]] = []
    for r in range(rows):
        for c in (0, cols - 1):
            if not closed[r, c]:
                closed[r, c] = True
                heapq.heappush(heap, (out[r, c], r, c))
    for c in range(cols):
        for r in (0, rows - 1):
            if not closed[r, c]:
                closed[r, c] = True
                heapq.heappush(heap, (out[r, c], r, c))
    while heap:
        h, r, c = heapq.heappop(heap)
        for dr, dc, _ in _D8:
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols and not closed[rr, cc]:
                closed[rr, cc] = True
                out[rr, cc] = max(out[rr, cc], h + eps)
                heapq.heappush(heap, (out[rr, cc], rr, cc))
    return out.astype(np.float32)


@dataclass
class Hydrology:
    filled: np.ndarray
    receiver: np.ndarray  # índice linear do pixel a jusante; -1 se saída
    accumulation: np.ndarray  # nº de pixéis a montante (inclui o próprio)


def flow(z: np.ndarray) -> Hydrology:
    """Direcção D8 e acumulação de fluxo."""
    filled = fill_depressions(z)
    rows, cols = filled.shape
    best = np.zeros((rows, cols), dtype=np.float32)
    recv = np.full((rows, cols), -1, dtype=np.int64)
    pad = np.pad(filled, 1, mode="edge")
    idx = np.arange(rows * cols).reshape(rows, cols)
    for dr, dc, dist in _D8:
        nb = pad[1 + dr : 1 + dr + rows, 1 + dc : 1 + dc + cols]
        drop = (filled - nb) / dist
        better = drop > best
        best = np.where(better, drop, best)
        nidx = np.roll(np.roll(idx, -dr, axis=0), -dc, axis=1)
        valid = np.ones((rows, cols), dtype=bool)
        if dr == -1:
            valid[0, :] = False
        if dr == 1:
            valid[-1, :] = False
        if dc == -1:
            valid[:, 0] = False
        if dc == 1:
            valid[:, -1] = False
        recv = np.where(better & valid, nidx, recv)

    flat_recv = recv.ravel()
    acc = np.ones(rows * cols, dtype=np.float64)
    for i in np.argsort(-filled.ravel(), kind="stable"):
        r = flat_recv[i]
        if r >= 0:
            acc[r] += acc[i]
    return Hydrology(filled, recv, acc.reshape(rows, cols).astype(np.float32))


def twi(acc: np.ndarray, slope: np.ndarray, res: float) -> np.ndarray:
    """Topographic Wetness Index: ln(a / tan(b)), a = área contribuinte específica."""
    a = acc * res  # (acc * res²) / res
    tan_b = np.tan(np.radians(np.maximum(slope, 0.1)))
    return np.log(a / tan_b).astype(np.float32)


def stream_mask(acc: np.ndarray, res: float, min_area_km2: float = 1.0) -> np.ndarray:
    return acc >= (min_area_km2 * 1e6) / (res**2)


def density(mask: np.ndarray, res: float, radius_m: float = 500.0) -> np.ndarray:
    """Fracção de pixéis marcados numa vizinhança gaussiana (proxy de densidade por área)."""
    return ndimage.gaussian_filter(mask.astype(np.float32), sigma=radius_m / res).astype(np.float32)


def basins(hyd: Hydrology, res: float, min_area_km2: float = 5.0) -> np.ndarray:
    """Sub-bacias: um rótulo por afluente com área ≥ limiar, cortado antes de cada confluência."""
    acc = hyd.accumulation.ravel()
    recv = hyd.receiver.ravel()
    big = acc >= (min_area_km2 * 1e6) / (res**2)
    upstream_big = np.zeros(acc.size, dtype=np.int32)
    for i in np.flatnonzero(big & (recv >= 0)):
        upstream_big[recv[i]] += 1
    outlet = big & ((recv < 0) | (upstream_big[np.where(recv >= 0, recv, 0)] >= 2))
    labels = np.zeros(acc.size, dtype=np.int32)
    next_id = 1
    for i in np.argsort(hyd.filled.ravel(), kind="stable"):  # a jusante primeiro
        if outlet[i]:
            labels[i] = next_id
            next_id += 1
        elif recv[i] >= 0:
            labels[i] = labels[recv[i]]
    return labels.reshape(hyd.accumulation.shape)


def lineaments(
    z: np.ndarray,
    res: float,
    azimuths: tuple[float, ...] = (0.0, 45.0, 90.0, 135.0),
    min_length_m: float = 500.0,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Segmentos candidatos a falhas/fracturas: bordas de hillshade multi-azimute + Hough.

    Devolve segmentos ((row0, col0), (row1, col1)). São candidatos, não falhas confirmadas.
    """
    segs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    min_px = max(int(min_length_m / res), 5)
    for az in azimuths:
        hs = hillshade(z, res, azimuth=az)
        edges = feature.canny(hs, sigma=2.0)
        found = transform.probabilistic_hough_line(
            edges, threshold=10, line_length=min_px, line_gap=3, rng=0
        )
        for (c0, r0), (c1, r1) in found:
            segs.append(((r0, c0), (r1, c1)))
    return segs


def lineament_density(
    segments: list[tuple[tuple[int, int], tuple[int, int]]],
    shape: tuple[int, int],
    res: float,
    radius_m: float = 1000.0,
) -> np.ndarray:
    canvas = np.zeros(shape, dtype=np.float32)
    for (r0, c0), (r1, c1) in segments:
        rr, cc = draw_line(r0, c0, r1, c1)
        ok = (rr >= 0) & (rr < shape[0]) & (cc >= 0) & (cc < shape[1])
        canvas[rr[ok], cc[ok]] = 1.0
    return density(canvas > 0, res, radius_m)
