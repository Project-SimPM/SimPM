"""Probability distributions and fitting helpers used throughout SimPM.

The functions in this module wrap common SciPy distributions with a lightweight
API tailored for simulation modeling. They make it easy to sample, plot, and
fit distributions while keeping consistent return types for downstream
components.
"""
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as st


@dataclass
class FitResult:
    """Container for the results of fitting a distribution.

    Attributes
    ----------
    dist_type : str
        The type of distribution fitted.
    params : tuple
        The parameters returned by the fitting routine.
    scipy_dist : scipy.stats.rv_continuous
        The fitted SciPy distribution instance.
    ks : float
        Kolmogorov–Smirnov statistic computed against the fitted CDF.
    wrapper : Optional[distribution]
        Convenience wrapper mirroring :mod:`simpm.dist` distribution classes.
    """

    dist_type: str
    params: Tuple[float, ...]
    scipy_dist: st.rv_continuous
    ks: float
    wrapper: Optional["distribution"] = None


def _validate_data(data: Iterable[float]) -> np.ndarray:
    """Validate and normalize user-provided data for fitting.

    Raises
    ------
    ValueError
        If the sequence is empty or contains NaN/inf values.
    """
    array = np.asarray(data, dtype=float).reshape(-1)
    if array.size == 0:
        raise ValueError("Data must contain at least one observation.")
    if np.isnan(array).any() or np.isinf(array).any():
        raise ValueError("Data must not contain NaN or infinite values.")
    return array


def fit(data: Iterable[float], dist_type: str, method: str = "mle") -> FitResult:
    """Fit a distribution on data and return a structured result.

    Parameters
    ----------
    data : array_like
        The data to fit the distribution to.
    dist_type : str
        The type of distribution to fit. Supported types are ``"triang"``,
        ``"norm"``, ``"beta"``, ``"trapz"``, and ``"expon"``.
    method : str, optional
        The method to use for fitting the distribution. Default is ``"mle"``
        (maximum likelihood estimation).

    Returns
    -------
    FitResult
        Structured fitting result containing the SciPy distribution, wrapper
        instance, and Kolmogorov–Smirnov statistic.

    Raises
    ------
    ValueError
        If the distribution type is not recognized or the input data are
        invalid.
    """

    normalized_type = str(dist_type).strip().lower()
    data_array = _validate_data(data)

    registry: Dict[str, Callable[[np.ndarray, str], FitResult]] = {
        "triang": fit_triang,
        "norm": fit_norm,
        "beta": fit_beta,
        "trapz": fit_trapz,
        "expon": fit_expon,
    }

    if normalized_type not in registry:
        raise ValueError(f"Distribution type '{dist_type}' is not recognized.")

    return registry[normalized_type](data_array, method)


def _validate_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive.")


def _compute_ks(data: np.ndarray, scipy_dist: st.rv_continuous) -> float:
    return st.kstest(data, scipy_dist.cdf)[0]


def fit_norm(data: np.ndarray, method: str = "mle") -> FitResult:
    """Fit a normal distribution to the provided data."""
    params = st.norm.fit(data, method=method)
    scipy_dist = st.norm(loc=params[0], scale=params[1])
    wrapper = make_norm(params[0], params[1])
    ks = _compute_ks(data, scipy_dist)
    return FitResult("norm", tuple(params), scipy_dist, ks, wrapper)


def fit_beta(data: np.ndarray, method: str = "mle") -> FitResult:
    """Fit a beta distribution to the provided data."""
    params = st.beta.fit(data, method=method)
    scipy_dist = st.beta(params[0], params[1], loc=params[2], scale=params[3])
    wrapper = make_beta(params[0], params[1], params[2], params[2] + params[3])
    ks = _compute_ks(data, scipy_dist)
    return FitResult("beta", tuple(params), scipy_dist, ks, wrapper)


def fit_triang(data: np.ndarray, method: str = "mle") -> FitResult:  # pylint: disable=unused-argument
    """Fit a triangular distribution to the provided data."""
    params = st.triang.fit(data)
    scipy_dist = st.triang(params[0], loc=params[1], scale=params[2])
    lower = params[1]
    upper = params[1] + params[2]
    mode = params[1] + params[0] * params[2]
    wrapper = make_triang(lower, mode, upper)
    ks = _compute_ks(data, scipy_dist)
    return FitResult("triang", tuple(params), scipy_dist, ks, wrapper)


def fit_trapz(data: np.ndarray, method: str = "mle") -> FitResult:
    """Fit a trapezoidal distribution to the provided data."""
    params = st.trapz.fit(data, method=method)
    scipy_dist = st.trapz(params[0], params[1], loc=params[2], scale=params[3])
    a = params[2]
    d = params[2] + params[3]
    b = a + params[0] * params[3]
    c = a + params[1] * params[3]
    wrapper = make_trapz(a, b, c, d)
    ks = _compute_ks(data, scipy_dist)
    return FitResult("trapz", tuple(params), scipy_dist, ks, wrapper)


def fit_expon(data: np.ndarray, method: str = "mle") -> FitResult:  # pylint: disable=unused-argument
    """Fit an exponential distribution with location fixed at zero."""
    params = st.expon.fit(data, floc=0)
    scipy_dist = st.expon(scale=params[1])
    wrapper = make_expon(params[1])
    ks = _compute_ks(data, scipy_dist)
    return FitResult("expon", (params[1],), scipy_dist, ks, wrapper)


class distribution:
    """Lightweight wrapper around SciPy distributions.

    All concrete distribution classes inherit from this base to expose a common
    API for sampling, plotting, and computing summary statistics.
    """

    def __init__(self):
        self.params = None
        self.dist_type = None
        self.dist = None
        self.ks = None

    def __str__(self):
        """Human-readable representation like 'dist.uniform(4, 5)'."""
        name = getattr(self, "dist_type", None) or self.__class__.__name__
        params = getattr(self, "params", None)

        if params is None:
            return f"dist.{name}"

        if not isinstance(params, (list, tuple)):
            params = [params]

        def _fmt(p):
            if isinstance(p, (int, float)):
                return f"{p:g}"
            return str(p)

        params_str = ", ".join(_fmt(p) for p in params)
        return f"dist.{name}({params_str})" if params_str else f"dist.{name}"

    __repr__ = __str__

    def sample(self):
        """Draw a single random variate from the distribution."""

        return self.dist.rvs()

    def samples(self, n):
        """Draw ``n`` random variates from the distribution."""

        return self.dist.rvs(n)

    def pdf_xy(self, size: int = 100):
        """Return x/y pairs for plotting the probability density function."""

        low = 0.00001
        high = 0.99999
        if self.dist_type in {"uniform", "triang", "trapz"}:
            low = 0
            high = 1
        x = np.linspace(self.dist.ppf(low), self.dist.ppf(high), size + 1)
        y = self.dist.pdf(x)
        return x, y

    def plot_pdf(self):
        """Plot the probability density function using matplotlib."""

        x, y = self.pdf_xy()
        plt.plot(x, y, "r")
        plt.xlabel("x")
        plt.ylabel("f(x)")
        plt.title("PDF")
        plt.show(block=True)
        return plt

    def cdf_xy(self, size: int):
        """Return x/y pairs for plotting the cumulative distribution function."""

        low = 0.00001
        high = 0.99999
        if self.dist_type in {"uniform", "triang", "trapz"}:
            low = 0
            high = 1
        x = np.linspace(self.dist.ppf(low), self.dist.ppf(high), size + 1)
        y = self.dist.cdf(x)
        return x, y

    def plot_cdf(self):
        """Plot the cumulative distribution function using matplotlib."""

        x, y = self.cdf_xy(100)
        plt.plot(x, y, "b")
        plt.xlabel("x")
        plt.ylabel("F(x)")
        plt.title("CDF")
        plt.show(block=True)
        return plt

    def percentile(self, q):
        """Return the value at percentile ``q`` (0–100)."""

        return self.dist.ppf(q / 100)

    def pdf(self, x):
        """Evaluate the probability density function at ``x``."""

        return self.dist.pdf(x)

    def cdf(self, x):
        """Evaluate the cumulative distribution function at ``x``."""

        return self.dist.cdf(x)

    def mean(self):
        """Return the distribution mean."""

        return self.dist.mean()

    def var(self):
        """Return the distribution variance."""

        return self.dist.var()

    def std(self):
        """Return the distribution standard deviation."""

        return self.dist.std()


class uniform(distribution):
    """Uniform distribution defined by lower/upper bounds."""

    def __init__(self, a, b):
        """Initialize the distribution with ``a`` (min) and ``b`` (max)."""
        if a >= b:
            raise ValueError("Lower bound must be less than upper bound.")
        self.dist_type = 'uniform'
        self.params = [a, b]
        self.dist = st.uniform(loc=a, scale=b - a)


def make_uniform(a: float, b: float) -> "uniform":
    """Create a uniform distribution with validation."""
    if a >= b:
        raise ValueError("Lower bound must be less than upper bound.")
    return uniform(a, b)


class norm(distribution):
    """
    Defines a normal distribution.
    """

    def __init__(self, mean, std):
        """
        Initializes the normal distribution.

        Parameters
        -----------
        mean : float
            The mean of the normal distribution.
        std : float
            The standard deviation of the normal distribution.
        """
        self.dist_type = 'norm'
        self.params = [mean, std]
        self.dist = st.norm(loc=mean, scale=std)


def make_norm(mean: float, std: float) -> "norm":
    """Create a normal distribution with validation."""
    _validate_positive(std, "Standard deviation")
    return norm(mean, std)


class triang(distribution):
    """
    Defines a triangular distribution.
    """

    def __init__(self, a, b, c):
        """
        Initializes the triangular distribution.

        Parameters
        -----------
        a : float
            The lower bound of the triangular distribution.
        b : float
            The mode of the triangular distribution.
        c : float
            The upper bound of the triangular distribution.
        """
        self.dist_type = 'triang'
        Loc = a
        Scale = c - a
        c_value = (b - a) / Scale
        self.params = [c_value, Loc, Scale]
        self.dist = st.triang(c_value, loc=Loc, scale=Scale)

    def __str__(self):
        # params = [c_value, Loc, Scale]
        c_value, Loc, Scale = self.params
        a = Loc
        c = Loc + Scale
        b = Loc + c_value * Scale
        return f"dist.triang({a:g}, {b:g}, {c:g})"


def make_triang(a: float, b: float, c: float) -> "triang":
    """Create a triangular distribution with validation."""
    if a >= c:
        raise ValueError("Lower bound must be less than upper bound.")
    if not (a <= b <= c):
        raise ValueError("Mode must lie between lower and upper bounds.")
    return triang(a, b, c)


class trapz(distribution):
    """
    Defines a trapezoidal distribution.
    """

    def __init__(self, a, b, c, d):
        """
        Initializes the trapezoidal distribution.

        Parameters
        -----------
        a : float
            The lower bound of the trapezoidal distribution.
        b : float
            The left corner of the trapezoidal distribution.
        c : float
            The right corner of the trapezoidal distribution.
        d : float
            The upper bound of the trapezoidal distribution.
        """
        self.dist_type = 'trapz'
        Loc = a
        Scale = d - a
        C = (b - a) / (d - a)
        D = (c - a) / (d - a)
        self.params = [C, D, Loc, Scale]
        self.dist = st.trapz(C, D, loc=Loc, scale=Scale)

    def __str__(self):
        # params = [C, D, Loc, Scale]
        C, D, Loc, Scale = self.params
        a = Loc
        d = Loc + Scale
        b = a + C * Scale
        c = a + D * Scale
        return f"dist.trapz({a:g}, {b:g}, {c:g}, {d:g})"


def make_trapz(a: float, b: float, c: float, d: float) -> "trapz":
    """Create a trapezoidal distribution with validation."""
    if a >= d:
        raise ValueError("Lower bound must be less than upper bound.")
    if not (a <= b <= c <= d):
        raise ValueError("Parameters must satisfy a <= b <= c <= d.")
    return trapz(a, b, c, d)


class beta(distribution):
    """
    Defines a beta distribution.
    """

    def __init__(self, a, b, minp, maxp):
        """
        Initializes the beta distribution.

        Parameters
        -----------
        a : float
            The first shape parameter of the beta distribution.
        b : float
            The second shape parameter of the beta distribution.
        minp : float
            The minimum value of the beta distribution.
        maxp : float
            The maximum value of the beta distribution.
        """
        self.dist_type = 'beta'
        Loc = minp
        Scale = maxp - minp
        self.params = [a, b, Loc, Scale]
        self.dist = st.beta(a, b, loc=Loc, scale=Scale)

    def __str__(self):
        # params = [a, b, Loc, Scale]
        a, b, Loc, Scale = self.params
        minp = Loc
        maxp = Loc + Scale
        return f"dist.beta({a:g}, {b:g}, {minp:g}, {maxp:g})"


def make_beta(a: float, b: float, minp: float, maxp: float) -> "beta":
    """Create a beta distribution with validation."""
    _validate_positive(a, "Alpha")
    _validate_positive(b, "Beta")
    if minp >= maxp:
        raise ValueError("Minimum bound must be less than maximum bound.")
    return beta(a, b, minp, maxp)


class expon(distribution):
    """
    Defines an exponential distribution.
    """

    def __init__(self, mean):
        """
        Initializes the exponential distribution.

        Parameters
        -----------
        mean : float
            The mean of the exponential distribution.
        """
        self.dist_type = 'expon'
        Scale = mean
        self.params = [Scale]
        self.dist = st.expon(scale=Scale)


def make_expon(mean: float) -> "expon":
    """Create an exponential distribution with validation."""
    _validate_positive(mean, "Mean")
    return expon(mean)


class empirical(distribution):
    """
    Defines an empirical distribution based on observed data.
    """

    def __init__(self, data):
        """
        Initializes the empirical distribution with observed data.

        Parameters
        -----------
        data : array_like
            The observed data to define the empirical distribution.
        """
        try:
            data = np.concatenate(data).ravel()
        except Exception:
            pass
        self.dist_type = 'empirical'
        self.params = None
        self.dist = None
        self.data = np.sort(data)

    def __str__(self):
        return f"dist.empirical(n={len(self.data)})"

    def cdf_xy(self):
        """
        Returns x, y numpy arrays for plotting the cumulative distribution function (CDF).
        """
        unique, counts = np.unique(self.data, return_counts=True)
        c = np.cumsum(counts)
        c = c / c[-1]
        return unique, c

    def plot_cdf(self):
        """
        Plots the cumulative distribution function (CDF) of the empirical distribution.
        """
        x, y = self.cdf_xy()
        plt.step(x, y)
        plt.show()

    def pdf_xy(self):
        """
        Returns x, y numpy arrays for plotting the probability density function (PDF).
        """
        bins = int(2 * len(self.data) ** (1 / 3))
        value, BinList = np.histogram(self.data, bins)
        value = value / len(self.data)
        l = BinList[-1] - BinList[0]
        n = len(BinList)
        width = l / n
        value = value / width
        BinList = BinList[:-1] + np.diff(BinList)[1] / 2
        return BinList, value

    def plot_pdf(self):
        """
        Plots the probability density function (PDF) of the empirical distribution.
        """
        x, y = self.pdf_xy()
        plt.bar(x, y, width=np.diff(x)[0])
        plt.show()

    def pdf(self, x):
        """
        Evaluates the probability density function (PDF) of the empirical distribution at the given point.
        """
        bins = int(2 * len(self.data) ** (1 / 3))
        value, BinList = np.histogram(self.data, bins)
        if x < BinList[0] or x > BinList[-1]:
            return 0
        i = 0
        bl = len(BinList)
        while x >= BinList[i] and i < bl:
            i += 1
        r = value[i - 1] / len(self.data)
        l = BinList[-1] - BinList[0]
        n = len(BinList)
        width = l / n
        r = r / width
        return r

    def cdf(self, x):
        """
        Evaluates the cumulative distribution function (CDF) of the empirical distribution at the given point.
        """
        if x > self.data[-1]:
            return 1
        i = 0
        while x >= self.data[i]:
            i += 1
        return i / len(self.data)

    def percentile(self, q):
        """
        Calculates the value corresponding to the given percentile of the empirical distribution.
        """
        return np.quantile(self.data, q)

    def samples(self, n):
        """
        Generates random samples from the empirical distribution.
        """
        return np.random.choice(self.data, n)

    def sample(self):
        """
        Generates a single random sample from the empirical distribution.
        """
        return np.random.choice(self.data)
