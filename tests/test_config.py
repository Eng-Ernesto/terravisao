import pytest

from terravisao.config import DEFAULT_WEIGHTS


@pytest.mark.parametrize("target", list(DEFAULT_WEIGHTS))
def test_weights_sum_to_one(target):
    assert sum(DEFAULT_WEIGHTS[target].values()) == pytest.approx(1.0)
