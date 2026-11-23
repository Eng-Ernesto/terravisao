import numpy as np

from terravisao.config import Level, Target
from terravisao.pipeline import confidence, final_class
from terravisao.zones import extract_zones


def test_extract_zones_ranks_by_score_and_area():
    classes = np.zeros((30, 30), dtype=np.uint8)
    score = np.zeros((30, 30), dtype=np.float32)
    classes[2:12, 2:12] = 2  # zona grande
    score[2:12, 2:12] = 0.9
    classes[20:24, 20:24] = 2  # zona pequena
    score[20:24, 20:24] = 0.7
    layers = {"iron_oxide": np.full((30, 30), 0.8, dtype=np.float32)}
    zones, labels = extract_zones(
        classes,
        score,
        layers,
        {"iron_oxide": 1.0},
        Target.IRON,
        pixel_area_km2=0.0004,
        min_area_km2=0.0,
    )
    assert [z.id for z in zones] == ["A", "B"]
    assert zones[0].area_km2 > zones[1].area_km2
    assert labels.max() == 2
    assert zones[0].contributions["iron_oxide"] > 0


def test_min_zone_area_filters_small():
    classes = np.zeros((20, 20), dtype=np.uint8)
    classes[5:8, 5:8] = 2
    score = np.where(classes == 2, 0.9, 0.0).astype(np.float32)
    zones, _ = extract_zones(
        classes, score, {}, {}, Target.GOLD, pixel_area_km2=0.0004, min_area_km2=1.0
    )
    assert zones == []


def test_final_class_rules():
    aoi = np.ones((10, 10), dtype=bool)
    low = np.zeros((10, 10), dtype=np.uint8)
    assert final_class(low, 0.0, aoi) == Level.LOW
    mid = low.copy()
    mid[:3, :] = 1  # 30 % em média
    assert final_class(mid, 0.0, aoi) == Level.MEDIUM
    assert final_class(low, 0.1, aoi) == Level.MEDIUM  # zona pequena
    assert final_class(low, 0.6, aoi) == Level.HIGH


def test_confidence_levels():
    assert confidence(0.3, True) == Level.LOW
    assert confidence(0.9, False) == Level.MEDIUM
    assert confidence(0.9, True) == Level.HIGH
