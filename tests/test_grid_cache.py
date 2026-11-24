import numpy as np

from terravisao import cache
from terravisao.aoi import validate_aoi
from terravisao.grid import Grid

AOI = {
    "type": "Polygon",
    "coordinates": [
        [[15.25, -12.95], [15.30, -12.95], [15.30, -12.90], [15.25, -12.90], [15.25, -12.95]]
    ],
}


def test_grid_covers_aoi_and_is_aligned():
    geom = validate_aoi(AOI)
    g = Grid.from_aoi(geom, 20.0, buffer_m=1000.0)
    assert g.epsg == 32733
    assert g.transform.c % 20 == 0 and g.transform.f % 20 == 0
    lon0, lat0, lon1, lat1 = g.bbox_wgs84()
    assert lon0 < 15.25 and lon1 > 15.30 and lat0 < -12.95 and lat1 > -12.90


def test_aoi_mask_inside_grid():
    geom = validate_aoi(AOI)
    g = Grid.from_aoi(geom, 20.0, buffer_m=1000.0)
    m = np.asarray(g.mask_of(geom))
    assert m.shape == g.shape and 0 < m.mean() < 1
    assert m.sum() * g.pixel_area_km2 > 20  # ~30 km²


def test_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("TERRAVISAO_CACHE_DIR", str(tmp_path))
    key = cache.make_key("x", a=1)
    assert cache.load(key) is None
    cache.save(key, {"z": np.arange(4)}, {"k": "v"})
    arrays, meta = cache.load(key)
    assert list(arrays["z"]) == [0, 1, 2, 3] and meta["k"] == "v"
    assert cache.make_key("x", a=1) == key and cache.make_key("x", a=2) != key
    assert cache.clear() == 2


def test_remote_reads_have_timeouts_and_retries():
    # Sem timeout, uma ligação parada pendura a análise para sempre (visto em 24/11).
    from terravisao.ingest._rio import GDAL_OPTIONS

    assert int(GDAL_OPTIONS["GDAL_HTTP_TIMEOUT"]) <= 60
    assert int(GDAL_OPTIONS["GDAL_HTTP_MAX_RETRY"]) >= 1
