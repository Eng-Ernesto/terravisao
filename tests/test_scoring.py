import numpy as np
import pytest

from terravisao import indices
from terravisao.scoring import classify, normalize, weighted_score


def test_normalize_range_and_nan():
    arr = np.array([[0.0, 5.0], [10.0, np.nan]], dtype=np.float32)
    out = normalize(arr, percentiles=(0, 100))
    assert out[0, 0] == 0.0 and out[1, 0] == 1.0
    assert np.isnan(out[1, 1])


def test_normalize_invert():
    out = normalize(np.array([0.0, 10.0]), percentiles=(0, 100), invert=True)
    assert list(out) == [1.0, 0.0]


def test_weighted_score_renormalizes_missing_layers():
    a = np.full((2, 2), 1.0, dtype=np.float32)
    score = weighted_score({"a": a}, {"a": 0.3, "b": 0.7})  # "b" ausente
    assert np.allclose(score, 1.0)


def test_weighted_score_requires_a_layer():
    with pytest.raises(ValueError):
        weighted_score({}, {"a": 1.0})


def test_classify_thresholds():
    score = np.array([0.1, 0.4, 0.64, 0.65, 0.9, np.nan])
    assert list(classify(score)) == [0, 1, 1, 2, 2, 255]


def test_indices_known_values():
    one = np.array([2.0], dtype=np.float32)
    two = np.array([1.0], dtype=np.float32)
    assert indices.iron_oxide(one, two)[0] == 2.0
    assert indices.ndvi(one, two)[0] == pytest.approx(1 / 3)
    assert np.isnan(indices.clay(one, np.array([0.0], dtype=np.float32))[0])


def test_smooth_ignores_nan_and_keeps_range():
    from terravisao.scoring import smooth

    s = np.full((20, 20), 0.8, dtype=np.float32)
    s[:, :3] = np.nan
    out = smooth(s, 2.0)
    assert np.isnan(out[:, :3]).all()
    assert np.allclose(out[:, 5:], 0.8, atol=1e-3)  # NaN não puxa o valor para baixo


def test_smooth_merges_fragments():
    from scipy import ndimage

    from terravisao.scoring import classify, smooth

    s = np.full((30, 30), 0.3, dtype=np.float32)
    s[10:20, 10:20] = 0.9
    s[14, 10:20] = 0.3  # linha de ruído que parte a mancha em duas
    _, raw_parts = ndimage.label(classify(s) == 2)
    _, smooth_parts = ndimage.label(classify(smooth(s, 1.5)) == 2)
    assert raw_parts == 2
    assert smooth_parts == 1
