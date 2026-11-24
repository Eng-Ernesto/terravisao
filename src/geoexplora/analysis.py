"""Análise de amostras: métrica (TREO), classes de anomalia, superfície, zonas, relações, modelo.

Tudo é calculado localmente e de forma explicável. As classes são relativas ao conjunto de dados
(quantis ou desvios), não são teores económicos.
"""

from __future__ import annotations

import string
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer
from scipy.spatial import cKDTree
from scipy.stats import binomtest, spearmanr
from shapely.geometry import MultiPoint, mapping
from sklearn.cluster import DBSCAN
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import balanced_accuracy_score
from sklearn.model_selection import GroupKFold

from . import ree
from .loaders import GridLayer, Points, sample_grid

CLASSES = ("baixa", "moderada", "elevada")
CLASS_LABEL = {"baixa": "Baixa", "moderada": "Moderada", "elevada": "Elevada"}


@dataclass
class Params:
    method: str = "quantis"  # "quantis" | "estatistico" (média + 1σ e + 2σ, em log)
    q_moderada: float = 0.50  # moderada: acima da mediana
    q_elevada: float = 0.85  # elevada: 15 % superior do conjunto
    cluster_eps_m: float | None = None  # None: automático
    cluster_min_samples: int = 4
    surface_cells: int = 150
    metric_element: str | None = None  # sem terras raras: elemento a analisar (ex. "Cu")


@dataclass
class Zone:
    id: str
    n_samples: int
    area_km2: float
    mean_value_ppm: float
    max_value_ppm: float
    ndpr_share: float | None
    centroid_lonlat: tuple[float, float]
    polygon: dict[str, Any]  # GeoJSON em WGS 84
    significant: bool = False  # maior do que o esperado por acaso (teste de permutação, p<0,05)


@dataclass
class Surface:
    array: np.ndarray  # TREO interpolado (ppm), NaN longe das amostras
    x0: float
    y1: float
    dx: float
    epsg: int


@dataclass
class Analysis:
    points: Points
    params: Params
    treo_label: str
    thresholds: dict[str, float]
    class_counts: dict[str, int]
    surface: Surface
    zones: list[Zone]
    correlations: list[dict[str, Any]]
    model: dict[str, Any]
    grids: dict[str, GridLayer] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        """Resumo estruturado, a única coisa que o assistente de IA vê."""
        df = self.points.df
        return {
            "conjunto": {
                "titulo": self.points.title,
                "ficticio": self.points.fictitious,
                "n_amostras": len(df),
                "elementos": self.points.elements,
                "covariaveis": self.points.covariates + [f"grelha:{g}" for g in self.grids],
                "metrica": self.treo_label,
            },
            "metrica_ppm": {
                "min": round(float(df["metrica_ppm"].min()), 1),
                "mediana": round(float(df["metrica_ppm"].median()), 1),
                "media": round(float(df["metrica_ppm"].mean()), 1),
                "max": round(float(df["metrica_ppm"].max()), 1),
            },
            "ndpr_sobre_treo": (
                round(float(df["ndpr_share"].mean()), 3) if "ndpr_share" in df else None
            ),
            "classificacao": {
                "metodo": self.params.method,
                "limiares_ppm": {k: round(v, 1) for k, v in self.thresholds.items()},
                "contagem": self.class_counts,
            },
            "zonas": [
                {
                    "id": z.id,
                    "n_amostras": z.n_samples,
                    "area_km2": round(z.area_km2, 3),
                    "valor_medio_ppm": round(z.mean_value_ppm, 1),
                    "valor_max_ppm": round(z.max_value_ppm, 1),
                    "ndpr_sobre_treo": None if z.ndpr_share is None else round(z.ndpr_share, 3),
                    "centro_lon_lat": [
                        round(z.centroid_lonlat[0], 4),
                        round(z.centroid_lonlat[1], 4),
                    ],
                    "significativa_vs_acaso": z.significant,
                }
                for z in self.zones
            ],
            "relacoes": self.correlations,
            "modelo": self.model,
            "avisos": self.warnings,
        }


# ------------------------------------------------------------------------------ classes
def classify(treo: pd.Series, params: Params) -> tuple[pd.Series, dict[str, float]]:
    """Classe de anomalia por amostra e os limiares (ppm de TREO)."""
    if params.method == "estatistico":
        logv = np.log10(treo.clip(lower=1e-6))
        mu, sd = float(logv.mean()), float(logv.std())
        t_mod, t_elev = 10 ** (mu + sd), 10 ** (mu + 2 * sd)
    else:
        t_mod = float(treo.quantile(params.q_moderada))
        t_elev = float(treo.quantile(params.q_elevada))
    cls = pd.Series(
        np.where(treo >= t_elev, "elevada", np.where(treo >= t_mod, "moderada", "baixa")),
        index=treo.index,
        name="classe",
    )
    return cls, {"moderada": t_mod, "elevada": t_elev}


# ---------------------------------------------------------------------------- superfície
def idw_surface(
    x: np.ndarray,
    y: np.ndarray,
    values: np.ndarray,
    cells: int = 150,
    k: int = 12,
    power: float = 2.0,
) -> Surface:
    """Interpolação por ponderação do inverso da distância, cortada longe das amostras."""
    pad = 0.05 * max(np.ptp(x), np.ptp(y))
    xmin, xmax, ymin, ymax = x.min() - pad, x.max() + pad, y.min() - pad, y.max() + pad
    dx = max(xmax - xmin, ymax - ymin) / cells
    cols, rows = int(np.ceil((xmax - xmin) / dx)), int(np.ceil((ymax - ymin) / dx))
    gx = xmin + (np.arange(cols) + 0.5) * dx
    gy = ymax - (np.arange(rows) + 0.5) * dx
    mx, my = np.meshgrid(gx, gy)
    tree = cKDTree(np.column_stack([x, y]))
    kk = min(k, len(x))
    dist, idx = tree.query(np.column_stack([mx.ravel(), my.ravel()]), k=kk)
    dist = np.maximum(dist.reshape(-1, kk), 1e-6)
    w = 1.0 / dist**power
    z = (w * values[idx.reshape(-1, kk)]).sum(axis=1) / w.sum(axis=1)
    nn = tree.query(np.column_stack([x, y]), k=2)[0][:, 1]
    far = dist[:, 0] > max(3 * float(np.median(nn)), 0.02 * max(np.ptp(x), np.ptp(y)))
    z[far] = np.nan
    return Surface(z.reshape(rows, cols).astype("float32"), float(xmin), float(ymax), float(dx), 0)


# ------------------------------------------------------------------------------- zonas
def _max_cluster(xy: np.ndarray, eps: float, min_samples: int) -> int:
    if len(xy) < min_samples:
        return 0
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(xy)
    found = labels[labels >= 0]
    return int(np.max(np.bincount(found))) if found.size else 0


def significance_threshold(
    all_xy: np.ndarray, n_high: int, eps: float, min_samples: int, n_perm: int = 99
) -> float:
    """Tamanho de grupo que o acaso só excede 5 % das vezes.

    Baralham-se as posições mantendo o número de amostras elevadas: se os dados não têm estrutura
    espacial, os grupos que aparecem não são maiores do que os desta distribuição.
    """
    rng = np.random.default_rng(0)
    sizes = [
        _max_cluster(all_xy[rng.choice(len(all_xy), n_high, replace=False)], eps, min_samples)
        for _ in range(n_perm)
    ]
    return float(np.percentile(sizes, 95))


def find_zones(df: pd.DataFrame, epsg: int, params: Params) -> list[Zone]:
    """Agrupa espacialmente as amostras de classe elevada (DBSCAN) e delimita cada grupo."""
    high = df[df["classe"] == "elevada"]
    if len(high) < params.cluster_min_samples:
        return []
    xy = high[["x", "y"]].to_numpy()
    all_xy = df[["x", "y"]].to_numpy()
    nn = cKDTree(all_xy).query(all_xy, k=2)[0][:, 1]
    eps = params.cluster_eps_m or max(600.0, 4.0 * float(np.median(nn)))
    labels = DBSCAN(eps=eps, min_samples=params.cluster_min_samples).fit_predict(xy)
    threshold = significance_threshold(all_xy, len(high), eps, params.cluster_min_samples)
    to_ll = Transformer.from_crs(epsg, 4326, always_xy=True)

    def to_wgs(coords: np.ndarray) -> np.ndarray:
        lon, lat = to_ll.transform(coords[:, 0], coords[:, 1])
        return np.column_stack([lon, lat])

    raw: list[tuple[float, Zone]] = []
    for lab in sorted(set(labels) - {-1}):
        grp = high[labels == lab]
        poly = MultiPoint(grp[["x", "y"]].to_numpy()).convex_hull.buffer(eps * 0.35)
        centre = poly.centroid
        clon, clat = to_ll.transform(centre.x, centre.y)
        ndpr = float(grp["ndpr_share"].mean()) if "ndpr_share" in grp else None
        zone = Zone(
            id="",
            n_samples=len(grp),
            area_km2=float(poly.area / 1e6),
            mean_value_ppm=float(grp["metrica_ppm"].mean()),
            max_value_ppm=float(grp["metrica_ppm"].max()),
            ndpr_share=ndpr,
            centroid_lonlat=(float(clon), float(clat)),
            polygon=dict(mapping(shapely.transform(poly, to_wgs))),
            significant=len(grp) > threshold,
        )
        raw.append((zone.mean_value_ppm * zone.n_samples, zone))
    raw.sort(key=lambda t: t[0], reverse=True)
    zones = [z for _, z in raw]
    for i, z in enumerate(zones):
        z.id = string.ascii_uppercase[i] if i < 26 else str(i + 1)
    return zones


# ---------------------------------------------------------------------------- relações
def _strength(rho: float, p: float) -> str:
    if p > 0.05 or abs(rho) < 0.2:
        return "sem relação relevante"
    return "forte" if abs(rho) >= 0.6 else "moderada" if abs(rho) >= 0.4 else "fraca"


def correlations(df: pd.DataFrame, names: list[str]) -> list[dict[str, Any]]:
    """Correlação de Spearman de cada covariável com o TREO (e com NdPr/TREO)."""
    out = []
    for name in names:
        ok = df[name].notna() & df["metrica_ppm"].notna()
        if ok.sum() < 10 or df.loc[ok, name].nunique() < 3:
            continue
        rho, p = spearmanr(df.loc[ok, name], df.loc[ok, "metrica_ppm"])
        out.append(
            {
                "variavel": name,
                "rho_spearman": round(float(rho), 3),
                "p_valor": round(float(p), 4),
                "leitura": _strength(float(rho), float(p)),
                "n": int(ok.sum()),
            }
        )
    return sorted(out, key=lambda r: abs(r["rho_spearman"]), reverse=True)


# -------------------------------------------------------------------------------- modelo
def spatial_model(df: pd.DataFrame, features: list[str]) -> dict[str, Any]:
    """Random Forest: a geofísica prevê a classe geoquímica? Validação cruzada por blocos espaciais.

    As variáveis que definem a classe (elementos, TREO) ficam de fora de propósito: se entrassem,
    o modelo «acertaria» por construção.
    """
    if not features:
        return {"executado": False, "motivo": "Sem variáveis geofísicas ou outras covariáveis."}
    data = df.dropna(subset=features + ["classe"])
    if len(data) < 60:
        return {"executado": False, "motivo": f"Poucas amostras com dados completos ({len(data)})."}
    block = max(np.ptp(data["x"]), np.ptp(data["y"])) / 4
    groups = (
        np.floor((data["x"] - data["x"].min()) / block).astype(int) * 100
        + np.floor((data["y"] - data["y"].min()) / block).astype(int)
    ).to_numpy()
    n_groups = len(np.unique(groups))
    if n_groups < 3:
        return {"executado": False, "motivo": "Amostras concentradas num só sítio."}
    X, y = data[features].to_numpy(), data["classe"].to_numpy()
    oof = np.empty(len(y), dtype=object)
    imp = np.zeros(len(features))
    folds = 0
    for tr, te in GroupKFold(n_splits=min(5, n_groups)).split(X, y, groups):
        rf = RandomForestClassifier(
            n_estimators=150, min_samples_leaf=3, random_state=0, n_jobs=1
        ).fit(X[tr], y[tr])
        oof[te] = rf.predict(X[te])
        imp += permutation_importance(
            rf, X[te], y[te], n_repeats=5, random_state=0, n_jobs=1
        ).importances_mean
        folds += 1
    hits = int((oof == y).sum())
    chance = float(pd.Series(y).value_counts(normalize=True).max())
    p = float(binomtest(hits, len(y), chance, alternative="greater").pvalue)
    beats = p < 0.05
    imp = imp / folds
    return {
        "executado": True,
        "n": len(y),
        "variaveis": features,
        "exatidao": round(hits / len(y), 3),
        "exatidao_equilibrada": round(float(balanced_accuracy_score(y, oof)), 3),
        "acaso": round(chance, 3),
        "p_valor_vs_acaso": round(p, 4),
        "supera_acaso": beats,
        "importancia": {
            f: round(float(v), 4)
            for f, v in sorted(zip(features, imp, strict=True), key=lambda t: -t[1])
        },
        "leitura": (
            "O modelo supera o acaso: a geofísica ajuda a prever onde a geoquímica é elevada."
            if beats
            else "O modelo NÃO supera o acaso: com estes dados, a geofísica não prevê a "
            "geoquímica. "
            "Não use este modelo para decidir."
        ),
    }


# --------------------------------------------------------------------------------- tudo
def run(
    points: Points, params: Params | None = None, grids: dict[str, GridLayer] | None = None
) -> Analysis:
    params = params or Params()
    df = points.df.copy()
    warnings = list(points.warnings)
    rees = ree.available(points.elements)
    if rees:
        df["metrica_ppm"] = ree.treo(df, points.elements)
        share = ree.ndpr_share(df, points.elements)
        if share is not None:
            df["ndpr_share"] = share
        label = ree.treo_label(points.elements)
        if label != "TREO":
            warnings.append(
                f"{label}: faltam elementos, por isso o valor é parcial e subestima o TREO."
            )
    else:
        others = [e for e in points.elements if f"{e}_ppm" in df]
        element = params.metric_element or (others[0] if others else None)
        if element is None or f"{element}_ppm" not in df:
            raise ValueError(
                "Sem colunas de elementos reconhecidas (ex.: Ce_ppm, Nd_ppm para terras raras; "
                "Cu_ppm, Li_ppm para outros minerais críticos)."
            )
        df["metrica_ppm"] = df[f"{element}_ppm"]
        label = f"{element} (ppm)"

    grids = grids or {}
    covariates = list(points.covariates)
    for name, layer in grids.items():
        col = f"grelha:{name}"
        df[col] = sample_grid(layer, df["lon"].to_numpy(), df["lat"].to_numpy())
        if df[col].notna().mean() < 0.5:
            warnings.append(f"A grelha «{name}» cobre menos de metade das amostras.")
        covariates.append(col)

    df["classe"], thresholds = classify(df["metrica_ppm"], params)
    counts = {c: int((df["classe"] == c).sum()) for c in CLASSES}
    surface = idw_surface(
        df["x"].to_numpy(), df["y"].to_numpy(), df["metrica_ppm"].to_numpy(), params.surface_cells
    )
    surface.epsg = points.epsg
    zones = find_zones(df, points.epsg, params)
    if not zones:
        warnings.append("Nenhuma zona de interesse: as amostras de classe elevada estão dispersas.")
    elif not any(z.significant for z in zones):
        warnings.append(
            "Nenhuma zona é maior do que o esperado por acaso (teste de permutação): "
            "a distribuição espacial das amostras elevadas não mostra concentração real."
        )
    corr = correlations(df, covariates)
    model = spatial_model(df, covariates)
    pts = Points(
        df,
        points.epsg,
        points.elements,
        covariates,
        points.source,
        points.title,
        points.fictitious,
        points.warnings,
    )
    return Analysis(
        pts, params, label, thresholds, counts, surface, zones, corr, model, grids, warnings
    )
