import numpy as np
import pytest

from terravisao import terrain


def plane(rows=40, cols=40, slope=0.1, res=30.0):
    """Plano inclinado para Sul->Norte: elevação aumenta com a linha."""
    r = np.arange(rows, dtype=np.float32)[:, None] * res * slope
    return np.repeat(r, cols, axis=1)


def test_slope_of_plane():
    z = plane(slope=0.1)
    s = terrain.slope_deg(z, 30.0)
    assert np.allclose(s[5:-5, 5:-5], np.degrees(np.arctan(0.1)), atol=0.01)


def test_hillshade_in_range():
    z = np.random.default_rng(0).random((30, 30)).astype(np.float32) * 10
    hs = terrain.hillshade(z, 30.0)
    assert hs.min() >= 0 and hs.max() <= 1


def test_fill_removes_pits():
    z = plane()
    z[20, 20] = z[20, 20] - 50  # poço
    filled = terrain.fill_depressions(z)
    assert filled[20, 20] > z[20, 20]


def test_flow_accumulates_downslope():
    # Plano que desce para a linha 0: o fluxo junta-se nessa borda.
    z = plane()
    hyd = terrain.flow(z)
    # Acumulação cresce para a linha baixa (0) e é conservada: máx = nº de pixéis da coluna
    assert hyd.accumulation[0].max() >= hyd.accumulation[39].max()
    assert hyd.accumulation.max() > 10


def test_flow_conserves_area_at_outlets():
    z = plane()
    hyd = terrain.flow(z)
    outlets = hyd.receiver < 0
    assert hyd.accumulation[outlets].sum() == pytest.approx(z.size)


def test_twi_higher_where_flat_and_wet():
    acc = np.array([[1.0, 100.0]], dtype=np.float32)
    sl = np.array([[10.0, 1.0]], dtype=np.float32)
    t = terrain.twi(acc, sl, 30.0)
    assert t[0, 1] > t[0, 0]


def test_basins_label_every_pixel_of_a_valley():
    # Vale em V: a água converge para o eixo e sai pela linha 0.
    cols = np.abs(np.arange(40) - 20)[None, :].astype(np.float32)
    z = np.repeat(np.arange(40, dtype=np.float32)[:, None], 40, axis=1) * 3 + cols * 5
    hyd = terrain.flow(z)
    labels = terrain.basins(hyd, res=30.0, min_area_km2=0.05)
    assert labels.max() >= 1
    assert (labels > 0).mean() > 0.9


def test_lineament_density_shape_and_range():
    segs = [((5, 5), (5, 35)), ((10, 10), (30, 10))]
    d = terrain.lineament_density(segs, (40, 40), 30.0, radius_m=60.0)
    assert d.shape == (40, 40)
    assert d.max() > d[0, 39]
