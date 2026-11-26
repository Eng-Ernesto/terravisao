import numpy as np
import pandas as pd
import pytest

from geoexplora import analysis, demo, geophysics, ree
from geoexplora.loaders import LoadError, read_points


def csv(rows: str) -> bytes:
    return rows.encode("utf-8")


# ------------------------------------------------------------------------------ terras raras
def test_treo_uses_oxide_factors_and_ndpr():
    df = pd.DataFrame({"Ce_ppm": [100.0], "La_ppm": [100.0], "Nd_ppm": [100.0], "Pr_ppm": [100.0]})
    els = ["Ce", "La", "Nd", "Pr"]
    expected = 100 * (1.2284 + 1.1728 + 1.1664 + 1.2082)
    assert ree.treo(df, els).iloc[0] == pytest.approx(expected)
    assert ree.ndpr_share(df, els).iloc[0] == pytest.approx(100 * (1.1664 + 1.2082) / expected)
    assert "parcial" in ree.treo_label(els)


def test_ndpr_is_none_without_pr():
    df = pd.DataFrame({"Ce_ppm": [1.0], "Nd_ppm": [1.0]})
    assert ree.ndpr_share(df, ["Ce", "Nd"]) is None


# ---------------------------------------------------------------------------------- leitura
def make_csv(n=40, extra="") -> bytes:
    rng = np.random.default_rng(1)
    lines = ["Amostra,X,Y,Ce_ppm,La_ppm,Cu_ppb" + (",Mag" if extra else "")]
    for i in range(n):
        x, y = 525000 + rng.uniform(0, 4000), 8572000 + rng.uniform(0, 4000)
        ce, la, cu = rng.uniform(50, 400), rng.uniform(20, 200), rng.uniform(1000, 5000)
        row = f"A{i},{x:.1f},{y:.1f},{ce:.1f},{la:.1f},{cu:.0f}"
        lines.append(row + (f",{rng.normal():.2f}" if extra else ""))
    return csv("\n".join(lines))


def test_read_points_detects_columns_units_and_crs():
    pts = read_points(make_csv(extra="x"), "dados.csv")
    assert set(pts.elements) == {"Ce", "La", "Cu"}
    assert pts.covariates == ["Mag"]
    assert pts.epsg == 32733
    assert pts.df["Cu_ppm"].between(1, 5).all()  # ppb convertido para ppm
    assert pts.df["lon"].between(15.0, 15.4).all() and pts.df["lat"].between(-13.0, -12.8).all()


def test_read_points_lonlat_and_outside_angola_warning():
    rows = "id,lon,lat,Ce_ppm\n" + "\n".join(
        f"s{i},30.{i:02d},10.{i:02d},{100 + i}" for i in range(20)
    )
    pts = read_points(csv(rows), "x.csv")
    assert any("fora de Angola" in w for w in pts.warnings)


def test_read_points_errors_are_readable():
    with pytest.raises(LoadError, match="coordenadas"):
        read_points(csv("a,b\n1,2\n3,4\n"), "x.csv")
    with pytest.raises(LoadError, match="pelo menos"):
        read_points(csv("X,Y,Ce_ppm\n525000,8572000,10\n"), "x.csv")


def test_geojson_points():
    import json

    feats = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [15.2 + i * 0.001, -12.9]},
            "properties": {"Ce_ppm": 100 + i},
        }
        for i in range(15)
    ]
    pts = read_points(
        json.dumps({"type": "FeatureCollection", "features": feats}).encode(), "p.geojson"
    )
    assert len(pts.df) == 15 and pts.elements == ["Ce"]


# ------------------------------------------------------------------------------- geofísica
def test_vertical_derivative_of_plane_wave():
    n, dx, wavelength = 128, 100.0, 3200.0
    x = np.arange(n) * dx
    field = np.sin(2 * np.pi * x / wavelength)[None, :].repeat(n, axis=0)
    dz = geophysics.vertical_derivative(field, dx, pad=False)
    expected = 2 * np.pi / wavelength
    assert np.nanmax(dz) == pytest.approx(expected, rel=0.02)


def test_analytic_signal_peaks_over_source():
    n = 101
    y, x = np.mgrid[0:n, 0:n] * 100.0
    bump = np.exp(-(((x - 5000) ** 2 + (y - 5000) ** 2) / (2 * 800**2)))
    asig = geophysics.analytic_signal(bump, 100.0)
    row, col = np.unravel_index(np.nanargmax(asig), asig.shape)
    assert abs(row - 50) <= 25 and abs(col - 50) <= 25
    assert geophysics.horizontal_gradient(np.ones((20, 20)), 10.0).max() == 0


# --------------------------------------------------------------------------------- análise
def test_team_data_shows_no_relation_and_no_significant_zone():
    folder = demo.list_datasets()["Longonjo: dados da equipa (fictícios)"]
    pts, grids, _ = demo.load(folder)
    a = analysis.run(pts, grids=grids)
    assert pts.fictitious and len(pts.df) == 500
    assert a.model["executado"] and not a.model["supera_acaso"]
    assert not any(z.significant for z in a.zones)
    assert all(r["leitura"] == "sem relação relevante" for r in a.correlations)


def test_coherent_model_finds_the_body_and_the_relation():
    folder = demo.list_datasets()["Longonjo: modelo sintético coerente (fictício)"]
    pts, grids, _ = demo.load(folder)
    a = analysis.run(pts, grids=grids)
    sig = [z for z in a.zones if z.significant]
    assert sig, "devia haver uma zona significativa sobre o corpo"
    lon, lat = sig[0].centroid_lonlat
    assert abs(lon - 15.255) < 0.03 and abs(lat - (-12.90)) < 0.03
    by_name = {r["variavel"]: r for r in a.correlations}
    assert by_name["Th_radiometria_ppm"]["rho_spearman"] > 0.4
    assert by_name["grelha:Magnética (nT)"]["rho_spearman"] > 0.25
    assert a.model["supera_acaso"]


def test_classes_follow_quantiles():
    s = pd.Series(np.arange(100.0))
    cls, th = analysis.classify(s, analysis.Params())
    assert (cls == "elevada").sum() == 15 and (cls == "baixa").sum() == 50
    assert th["elevada"] > th["moderada"]


def test_generic_critical_mineral_without_rare_earths():
    pts = read_points(make_csv(n=60), "cu.csv")
    pts.df = pts.df.drop(columns=["Ce_ppm", "La_ppm"])
    pts.elements = ["Cu"]
    a = analysis.run(pts)
    assert a.treo_label == "Cu (ppm)"
    assert "ndpr_sobre_treo" in a.summary() and a.summary()["ndpr_sobre_treo"] is None


def test_summary_is_json_serialisable():
    import json

    folder = demo.list_datasets()["Longonjo: modelo sintético coerente (fictício)"]
    pts, grids, _ = demo.load(folder)
    json.dumps(analysis.run(pts, grids=grids).summary())


def test_excel_semicolon_and_decimal_comma():
    # Excel em português: separador «;» e vírgula decimal
    rows = ["Amostra;X;Y;Ce_ppm;La_ppm"]
    for i in range(20):
        rows.append(f"S{i:02d};{525000 + i * 37},5;{8572000 + i * 41},25;{100 + i},5;{50 + i},2")
    pts = read_points(csv("\n".join(rows)), "excel.csv", epsg=32733)
    assert len(pts.df) == 20
    assert pts.df["Ce_ppm"].iloc[0] == pytest.approx(100.5)
    assert pts.df["id"].iloc[0] == "S00"  # identificadores não são convertidos
    assert pts.df["lat"].between(-13.0, -12.8).all()


# ----------------------------------------------------------------- shapefile (zip de amostras)
def _shapefile_zip_bytes(n=20) -> bytes:
    import io
    import tempfile
    import zipfile
    from pathlib import Path

    import geopandas as gpd

    rng = np.random.default_rng(2)
    gdf = gpd.GeoDataFrame(
        {"Ce_ppm": rng.uniform(50, 400, n), "La_ppm": rng.uniform(20, 200, n)},
        geometry=gpd.points_from_xy(
            15.2 + rng.uniform(0, 0.05, n), -12.9 + rng.uniform(0, 0.05, n)
        ),
        crs=4326,
    )
    with tempfile.TemporaryDirectory() as tmp:
        gdf.to_file(Path(tmp) / "amostras.shp")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for f in Path(tmp).glob("amostras.*"):
                zf.write(f, f.name)
        return buf.getvalue()


def test_shapefile_zip_is_read_correctly():
    pytest.importorskip("geopandas")
    pts = read_points(_shapefile_zip_bytes(), "amostras.zip")
    assert len(pts.df) == 20 and pts.elements == ["Ce", "La"]
    assert pts.df["lon"].between(15.0, 15.4).all()


def test_non_shapefile_zip_gives_a_clear_error():
    """Reproduz o engano real: carregar o terravisao_dados.zip (GeoTIFF/GeoJSON) por engano."""
    pytest.importorskip("geopandas")
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("zones_terras_raras.geojson", '{"type":"FeatureCollection","features":[]}')
        zf.writestr("run.json", "{}")
    with pytest.raises(LoadError, match="TerraVisão"):
        read_points(buf.getvalue(), "terravisao_dados.zip")


def test_truly_invalid_zip_gives_a_clear_error():
    with pytest.raises(LoadError, match="não é um .zip válido"):
        read_points(b"isto nao e um zip", "dados.zip")
