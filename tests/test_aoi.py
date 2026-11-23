import pytest

from terravisao.aoi import AoiError, area_km2, utm_epsg, validate_aoi


def square(lon, lat, size):
    return {
        "type": "Polygon",
        "coordinates": [
            [[lon, lat], [lon + size, lat], [lon + size, lat + size], [lon, lat + size], [lon, lat]]
        ],
    }


def test_utm_zone_for_angola():
    assert utm_epsg(15.0, -13.0) == 32733  # Longonjo / Huambo
    assert utm_epsg(20.0, -9.0) == 32734  # Lunda


def test_valid_small_aoi():
    geom = validate_aoi(square(14.5, -15.0, 0.05))
    assert 20 < area_km2(geom) < 40  # ~5.4 km x 5.4 km


def test_rejects_outside_angola():
    with pytest.raises(AoiError, match="dentro de Angola"):
        validate_aoi(square(30.0, 10.0, 0.05))


def test_rejects_too_large():
    with pytest.raises(AoiError, match="O máximo"):
        validate_aoi(square(14.0, -15.0, 1.0))


def test_rejects_self_intersection():
    bowtie = {
        "type": "Polygon",
        "coordinates": [[[14, -15], [14.1, -15.1], [14.1, -15], [14, -15.1], [14, -15]]],
    }
    with pytest.raises(AoiError, match="auto-intersecções"):
        validate_aoi(bowtie)


def test_rejects_non_polygon():
    with pytest.raises(AoiError):
        validate_aoi({"type": "Point", "coordinates": [14.5, -15.0]})
