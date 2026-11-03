"""Linear angular PDFs require integrating the quadratic transport product."""

from __future__ import annotations

import numpy as np
import pytest

from pyradmc.data.tabulated.eedl import _mean_one_minus_mu


def test_linear_pdf_transport_moment_is_analytic() -> None:
    """For p(mu)=2+mu, integral p=4 and integral (1-mu)*p=10/3."""
    assert _mean_one_minus_mu(np.array([-1.0, 1.0]), np.array([1.0, 3.0])) == pytest.approx(
        5.0 / 6.0
    )


def test_angular_cell_subdivision_preserves_the_integral() -> None:
    """Adding nodes to the same linear PDF cannot change its transport moment."""
    mu = np.array([-1.0, -0.9, 0.1, 0.999, 1.0])
    assert _mean_one_minus_mu(mu, 2.0 + mu) == pytest.approx(5.0 / 6.0, rel=2e-15)


def test_piecewise_linear_transport_matches_independent_gauss_rule() -> None:
    """A four-point Gauss rule independently integrates each quadratic product."""
    mu = np.array([-1.0, -0.7, 0.4, 0.98, 0.999999])
    probability = np.array([0.1, 0.4, 1.0, 30.0, 1000.0])
    nodes, weights = np.polynomial.legendre.leggauss(4)
    norm = first = 0.0
    for a, b, pa, pb in zip(mu[:-1], mu[1:], probability[:-1], probability[1:], strict=True):
        x = (a + b) / 2 + (b - a) / 2 * nodes
        pdf = pa + (pb - pa) * (x - a) / (b - a)
        norm += (b - a) / 2 * np.dot(weights, pdf)
        first += (b - a) / 2 * np.dot(weights, (1 - x) * pdf)
    assert _mean_one_minus_mu(mu, probability) == pytest.approx(first / norm, rel=2e-15)
