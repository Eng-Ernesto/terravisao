"""Terras raras: conversão para óxidos (TREO) e razões úteis para ímanes permanentes.

Factores estequiométricos padrão elemento -> óxido comercial. O TREO calculado só com os
elementos presentes nos dados é um TREO **parcial** e é identificado como tal.
"""

from __future__ import annotations

import pandas as pd

# massa de óxido por massa de elemento
OXIDE_FACTOR: dict[str, float] = {
    "La": 1.1728,  # La2O3
    "Ce": 1.2284,  # CeO2
    "Pr": 1.2082,  # Pr6O11
    "Nd": 1.1664,  # Nd2O3
    "Sm": 1.1596,  # Sm2O3
    "Eu": 1.1579,  # Eu2O3
    "Gd": 1.1526,  # Gd2O3
    "Tb": 1.1762,  # Tb4O7
    "Dy": 1.1477,  # Dy2O3
    "Ho": 1.1455,  # Ho2O3
    "Er": 1.1435,  # Er2O3
    "Tm": 1.1421,  # Tm2O3
    "Yb": 1.1387,  # Yb2O3
    "Lu": 1.1371,  # Lu2O3
    "Y": 1.2699,  # Y2O3
}
OXIDE_NAME: dict[str, str] = {
    "La": "La₂O₃",
    "Ce": "CeO₂",
    "Pr": "Pr₆O₁₁",
    "Nd": "Nd₂O₃",
    "Sm": "Sm₂O₃",
    "Eu": "Eu₂O₃",
    "Gd": "Gd₂O₃",
    "Tb": "Tb₄O₇",
    "Dy": "Dy₂O₃",
    "Ho": "Ho₂O₃",
    "Er": "Er₂O₃",
    "Tm": "Tm₂O₃",
    "Yb": "Yb₂O₃",
    "Lu": "Lu₂O₃",
    "Y": "Y₂O₃",
}
LREE = ("La", "Ce", "Pr", "Nd", "Sm")
MAGNET_ELEMENTS = ("Nd", "Pr")  # ímanes permanentes (turbinas eólicas, motores eléctricos)


def available(elements: list[str]) -> list[str]:
    """Elementos de terras raras reconhecidos, pela ordem da tabela periódica."""
    return [e for e in OXIDE_FACTOR if e in elements]


def treo(df: pd.DataFrame, elements: list[str]) -> pd.Series:
    """TREO (ppm de óxidos) a partir de colunas `<El>_ppm`. Parcial se faltarem elementos."""
    cols = available(elements)
    if not cols:
        raise ValueError("Sem elementos de terras raras reconhecidos nos dados.")
    total = sum(df[f"{e}_ppm"] * OXIDE_FACTOR[e] for e in cols)
    return pd.Series(total, index=df.index, name="treo_ppm", dtype="float64")


def ndpr_share(df: pd.DataFrame, elements: list[str]) -> pd.Series | None:
    """NdPr/TREO (fracção de óxidos de Nd e Pr no TREO); None se faltar Nd ou Pr."""
    if not all(e in elements for e in MAGNET_ELEMENTS):
        return None
    magnet = sum(df[f"{e}_ppm"] * OXIDE_FACTOR[e] for e in MAGNET_ELEMENTS)
    return pd.Series(magnet / treo(df, elements), index=df.index, name="ndpr_share")


def treo_label(elements: list[str]) -> str:
    cols = available(elements)
    all_ree = len(cols) == len(OXIDE_FACTOR)
    return "TREO" if all_ree else f"TREO parcial ({', '.join(cols)})"
