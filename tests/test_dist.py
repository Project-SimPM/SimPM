import numpy as np
import pytest

import simpm.dist as dist


def test_fit_normal_distribution_recovers_parameters():
    rng = np.random.default_rng(42)
    data = rng.normal(loc=5.0, scale=2.0, size=2000)

    fitted = dist.fit(data, "norm")

    assert isinstance(fitted, dist.norm)
    assert fitted.dist_type == "norm"
    assert fitted.dist.mean() == pytest.approx(5.0, rel=0.05, abs=0.25)
    assert fitted.dist.std() == pytest.approx(2.0, rel=0.05, abs=0.25)


def test_fit_unknown_distribution_raises_error():
    with pytest.raises(TypeError):
        dist.fit([1, 2, 3], "does_not_exist")
