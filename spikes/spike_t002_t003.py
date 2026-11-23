"""Spikes T-002 (Sentinel-2 via STAC) e T-003 (DEM, declive, hillshade).

AOI de teste: ~5x5 km perto de Longonjo (Huambo). Fonte: Earth Search (AWS), sem autenticação.
Uso: python spikes/spike_t002_t003.py
"""

from __future__ import annotations

import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import odc.stac
from pystac_client import Client

from terravisao import indices

OUT = Path("data/cache/spikes")
OUT.mkdir(parents=True, exist_ok=True)
BBOX = (15.25, -12.95, 15.30, -12.90)  # lon_min, lat_min, lon_max, lat_max
URL = "https://earth-search.aws.element84.com/v1"


def main() -> None:
    # Dados públicos na AWS: acesso sem assinatura e sem credenciais.
    odc.stac.configure_rio(cloud_defaults=True, aws={"aws_unsigned": True})
    cat = Client.open(URL)
    t0 = time.time()
    items = list(
        cat.search(
            collections=["sentinel-2-l2a"],
            bbox=BBOX,
            datetime="2024-05-01/2025-09-30",
            query={"eo:cloud_cover": {"lt": 20}},
        ).items()
    )
    items = [i for i in items if i.datetime and i.datetime.month in (5, 6, 7, 8, 9)]
    print(f"S2: {len(items)} cenas (seca, <20% nuvens) em {time.time() - t0:.1f}s")
    if not items:
        raise SystemExit("sem cenas")
    # Só as cenas com menos nuvens: carregar todas é lento e desnecessário para a mediana.
    items.sort(key=lambda i: i.properties.get("eo:cloud_cover", 100))
    items = items[:12]
    print(f"a usar {len(items)} cenas")

    t0 = time.time()
    ds = odc.stac.load(
        items,
        bands=["blue", "red", "nir08", "swir16", "swir22", "scl"],
        bbox=BBOX,
        crs="EPSG:32733",
        resolution=20,
        chunks={},
    ).compute()
    print(f"carregado {dict(ds.sizes)} em {time.time() - t0:.1f}s")

    # Máscara SCL: 4 vegetação, 5 solo nu, 6 água, 7 não classificado baixo; excluir 3,8,9,10,11
    good = ds.scl.isin([4, 5, 7])
    refl = {
        b: ds[b].where(good).astype("float32") for b in ["blue", "red", "nir08", "swir16", "swir22"]
    }
    comp = {k: v.median("time", skipna=True).values for k, v in refl.items()}
    valid = np.isfinite(comp["red"]).mean()
    print(f"fracção válida do composto: {valid:.2%}")

    layers = {
        "iron_oxide": indices.iron_oxide(comp["red"], comp["blue"]),
        "ferrous": indices.ferrous(comp["swir16"], comp["nir08"]),
        "clay": indices.clay(comp["swir16"], comp["swir22"]),
    }
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, (name, arr) in zip(axes, layers.items(), strict=True):
        lo, hi = np.nanpercentile(arr, [2, 98])
        ax.imshow(arr, vmin=lo, vmax=hi, cmap="viridis")
        ax.set_title(f"{name} (p2={lo:.2f}, p98={hi:.2f})")
        ax.axis("off")
    fig.savefig(OUT / "t002_indices.png", dpi=90, bbox_inches="tight")

    # T-003: DEM Copernicus GLO-30 (SRTM equivalente aberto na AWS)
    t0 = time.time()
    dem_items = list(cat.search(collections=["cop-dem-glo-30"], bbox=BBOX).items())
    dem = odc.stac.load(dem_items, bbox=BBOX, crs="EPSG:32733", resolution=30, chunks={}).compute()
    z = dem["data"].isel(time=0).values.astype("float32")
    print(f"DEM {z.shape} em {time.time() - t0:.1f}s, elev {np.nanmin(z):.0f}-{np.nanmax(z):.0f} m")
    gy, gx = np.gradient(z, 30.0)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    az, alt = np.radians(315), np.radians(45)
    aspect = np.arctan2(-gx, gy)
    hs = np.sin(alt) * np.cos(np.arctan(np.hypot(gx, gy))) + np.cos(alt) * np.sin(
        np.arctan(np.hypot(gx, gy))
    ) * np.cos(az - aspect)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, arr, title, cmap in zip(
        axes,
        [z, slope, hs],
        ["elevação (m)", "declive (°)", "hillshade"],
        ["terrain", "magma", "gray"],
        strict=True,
    ):
        ax.imshow(arr, cmap=cmap)
        ax.set_title(title)
        ax.axis("off")
    fig.savefig(OUT / "t003_terrain.png", dpi=90, bbox_inches="tight")
    print("figuras em", OUT)


if __name__ == "__main__":
    main()
