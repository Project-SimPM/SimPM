import numpy as np
import pytest

import simpm.dist as dist


def test_fit_normal_distribution_recovers_parameters():
    rng = np.random.default_rng(42)
    data = rng.normal(loc=5.0, scale=2.0, size=2000)

    fitted = dist.fit(data, "norm")

    assert isinstance(fitted, dist.FitResult)
    assert isinstance(fitted.wrapper, dist.norm)
    assert fitted.dist_type == "norm"
    assert fitted.scipy_dist.mean() == pytest.approx(5.0, rel=0.05, abs=0.25)
    assert fitted.scipy_dist.std() == pytest.approx(2.0, rel=0.05, abs=0.25)


def test_fit_unknown_distribution_raises_error():
    with pytest.raises(ValueError):
        dist.fit([1, 2, 3], "does_not_exist")


def test_fit_validates_data():
    with pytest.raises(ValueError):
        dist.fit([], "norm")

    with pytest.raises(ValueError):
        dist.fit([1.0, np.nan], "norm")


def test_fit_reports_ks_statistic():
    rng = np.random.default_rng(7)
    data = rng.beta(2.0, 5.0, size=500)

    fitted = dist.fit(data, "beta")

    expected_ks = dist.st.kstest(data, fitted.scipy_dist.cdf)[0]
    assert fitted.ks == pytest.approx(expected_ks)


def test_convenience_builders_validate():
    with pytest.raises(ValueError):
        dist.make_beta(-1, 2, 0, 1)

    with pytest.raises(ValueError):
        dist.make_triang(1, 0, 2)

    expo = dist.make_expon(2.5)
    assert isinstance(expo, dist.expon)
