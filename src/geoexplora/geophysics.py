"""Derivadas de grelhas de campo potencial (magnetometria, gravimetria) por FFT.

Calculam-se sobre a grelha carregada pelo utilizador, em metros. A redução ao pólo (RTP) não
está incluída: exige inclinação e declinação do campo e validação pelo geofísico.
"""

from __future__ import annotations

import numpy as np


def _filled(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Substitui NaN pela média para a FFT e devolve também a máscara original."""
    bad = ~np.isfinite(arr)
    out = arr.astype("float64").copy()
    out[bad] = np.nanmean(arr) if (~bad).any() else 0.0
    return out, bad


def _taper(n: int, frac: float = 0.1) -> np.ndarray:
    k = max(int(n * frac), 1)
    w = np.ones(n)
    ramp = 0.5 * (1 - np.cos(np.pi * np.arange(k) / k))
    w[:k], w[-k:] = ramp, ramp[::-1]
    return w


def vertical_derivative(grid: np.ndarray, dx: float, pad: bool = True) -> np.ndarray:
    """1.ª derivada vertical de um campo potencial (domínio da frequência: |k|·F).

    `pad=True` reflecte e suaviza as bordas para reduzir efeitos de fronteira.
    """
    data, bad = _filled(grid)
    rows, cols = data.shape
    if pad:
        py, px = rows // 4, cols // 4
        data = np.pad(data - data.mean(), ((py, py), (px, px)), mode="reflect")
        data = data * np.outer(_taper(data.shape[0]), _taper(data.shape[1]))
    ky = 2 * np.pi * np.fft.fftfreq(data.shape[0], d=dx)
    kx = 2 * np.pi * np.fft.fftfreq(data.shape[1], d=dx)
    k = np.hypot(*np.meshgrid(kx, ky))
    dz = np.real(np.fft.ifft2(np.fft.fft2(data) * k))
    if pad:
        dz = dz[py : py + rows, px : px + cols]
    dz[bad] = np.nan
    return dz.astype("float32")


def horizontal_gradient(grid: np.ndarray, dx: float) -> np.ndarray:
    """Módulo do gradiente horizontal (realça bordas de fontes)."""
    gy, gx = np.gradient(grid.astype("float64"), dx)
    return np.hypot(gx, gy).astype("float32")


def analytic_signal(grid: np.ndarray, dx: float, pad: bool = True) -> np.ndarray:
    """Amplitude do sinal analítico: √(dT/dx² + dT/dy² + dT/dz²); máxima sobre a fonte."""
    gy, gx = np.gradient(grid.astype("float64"), dx)
    gz = vertical_derivative(grid, dx, pad=pad).astype("float64")
    return np.sqrt(gx**2 + gy**2 + gz**2).astype("float32")


def derivatives(grid: np.ndarray, dx: float) -> dict[str, np.ndarray]:
    return {
        "Primeira derivada vertical": vertical_derivative(grid, dx),
        "Gradiente horizontal": horizontal_gradient(grid, dx),
        "Sinal analítico": analytic_signal(grid, dx),
    }
