"""Gera os conjuntos de demonstração do GeoExplora IA (todos FICTÍCIOS).

1. longonjo_equipa: os ficheiros recebidos da equipa, com o deslocamento rígido de coordenadas
   que a própria equipa usou (as coordenadas originais caem a ~7,2° S, fora de Longonjo).
2. longonjo_modelo: modelo sintético coerente (corpo carbonatítico fictício onde as terras raras
   coincidem com um alto magnético e com tório), para mostrar o motor quando há relação nos dados.

Uso: python scripts/make_demo_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "geoexplora" / "demo"
# Ficheiro recebido da equipa (pasta local `informacao/`, fora do git).
SRC = ROOT / "informacao" / "dados_sinteticos_longonjo.csv"
DX, DY = 22536.0, -631168.5  # deslocamento rígido usado pela equipa (ficheiro «ajustados»)
EPSG = 32733


def team_dataset() -> None:
    d = pd.read_csv(SRC)
    out = pd.DataFrame(
        {
            "Amostra": d["Amostra"],
            "X": (d["X_teste"] + DX).round(1),
            "Y": (d["Y_teste"] + DY).round(1),
            "Ce_ppm": d["Ce_ppm"].round(1),
            "La_ppm": d["La_ppm"].round(1),
            "Nd_ppm": d["Nd_ppm"].round(1),
            "Pr_ppm": d["Pr_ppm"].round(1),
            "Anomalia_magnetica_teste": d["Anomalia_magnetica_teste"].round(1),
        }
    )
    folder = OUT / "longonjo_equipa"
    folder.mkdir(parents=True, exist_ok=True)
    out.to_csv(folder / "amostras.csv", index=False)
    (folder / "meta.json").write_text(
        json.dumps(
            {
                "title": "Longonjo: dados da equipa (fictícios)",
                "fictitious": True,
                "epsg": EPSG,
                "note": "500 amostras fictícias fornecidas pela equipa. Coordenadas deslocadas "
                "(+22 536 m em X, −631 169 m em Y) para Longonjo, como na versão «ajustados». "
                "Os valores são aleatórios, sem relação espacial nem com a anomalia magnética.",
                "grids": {},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("equipa:", len(out), "amostras")


def gauss(
    x: np.ndarray, y: np.ndarray, cx: float, cy: float, sa: float, sb: float, ang: float
) -> np.ndarray:
    c, s = np.cos(np.radians(ang)), np.sin(np.radians(ang))
    u, v = (x - cx) * c + (y - cy) * s, -(x - cx) * s + (y - cy) * c
    return np.exp(-0.5 * ((u / sa) ** 2 + (v / sb) ** 2))


def model_dataset() -> None:
    rng = np.random.default_rng(42)
    d = pd.read_csv(SRC)
    xmin, xmax = d["X_teste"].min() + DX, d["X_teste"].max() + DX
    ymin, ymax = d["Y_teste"].min() + DY, d["Y_teste"].max() + DY
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    n = 500
    x, y = rng.uniform(xmin, xmax, n), rng.uniform(ymin, ymax, n)

    # corpo carbonatítico fictício (elongado NE) e um corpo secundário menor
    body = gauss(x, y, cx, cy, 1800, 1100, 40) + 0.5 * gauss(
        x, y, cx - 3000, cy + 2500, 700, 700, 0
    )
    total = 140 * np.exp(0.35 * rng.standard_normal(n)) * (1 + 7 * body)
    j = lambda: np.clip(rng.normal(1, 0.07, n), 0.7, 1.3)  # noqa: E731
    ce = total * 0.46 * j()
    la = total * 0.27 * j()
    nd = total * (0.19 + 0.03 * np.clip(body, 0, 1)) * j()
    pr = total * (0.055 + 0.01 * np.clip(body, 0, 1)) * j()
    th = np.clip(18 + 55 * body + rng.normal(0, 6, n), 2, None)
    k = np.clip(1.2 + rng.normal(0, 0.3, n), 0.2, None)

    folder = OUT / "longonjo_modelo"
    folder.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "Amostra": [f"M{i + 1:03d}" for i in range(n)],
            "X": x.round(1),
            "Y": y.round(1),
            "Ce_ppm": ce.round(1),
            "La_ppm": la.round(1),
            "Nd_ppm": nd.round(1),
            "Pr_ppm": pr.round(1),
            "Th_radiometria_ppm": th.round(1),
            "K_radiometria_pct": k.round(2),
        }
    ).to_csv(folder / "amostras.csv", index=False)

    # grelha magnética (nT) de 100 m: alto sobre o corpo, lobo negativo a norte, corpo secundário,
    # tendência regional suave e ruído correlacionado
    res = 100.0
    pad = 1500.0
    x0, y1 = xmin - pad, ymax + pad
    cols, rows = int((xmax - xmin + 2 * pad) / res), int((ymax - ymin + 2 * pad) / res)
    gx, gy = np.meshgrid(x0 + (np.arange(cols) + 0.5) * res, y1 - (np.arange(rows) + 0.5) * res)
    mag = (
        260 * gauss(gx, gy, cx - 250, cy - 150, 1000, 700, 40)
        - 90 * gauss(gx, gy, cx + 600, cy + 1000, 800, 600, 40)
        + 45 * gauss(gx, gy, cx - 3000, cy + 2500, 600, 600, 0)
        + 0.0015 * (gx - cx)
        + gaussian_filter(rng.normal(0, 14, gx.shape), 3)
    ).astype("float32")
    with rasterio.open(
        folder / "magnetica_nT.tif",
        "w",
        driver="GTiff",
        height=rows,
        width=cols,
        count=1,
        dtype="float32",
        crs=f"EPSG:{EPSG}",
        transform=from_origin(x0, y1, res, res),
        nodata=-9999.0,
        compress="deflate",
    ) as dst:
        dst.write(mag, 1)

    (folder / "meta.json").write_text(
        json.dumps(
            {
                "title": "Longonjo: modelo sintético coerente (fictício)",
                "fictitious": True,
                "epsg": EPSG,
                "note": "Dados GERADOS por nós (scripts/make_demo_data.py, semente 42): corpo "
                "carbonatítico fictício onde as terras raras coincidem com um alto magnético e com "
                "tório. Serve só para demonstrar o motor quando há relação nos dados.",
                "grids": {"Magnética (nT)": "magnetica_nT.tif"},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("modelo:", n, "amostras; grelha", rows, "x", cols)


if __name__ == "__main__":
    team_dataset()
    model_dataset()
