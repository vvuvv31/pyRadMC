"""A positive residual mass path must retain the stopping endpoint."""

import math

import numpy as np
import pytest

from pyradmc.data.tables import lookup_inverse_restricted_range, lookup_loglinear_2d


@pytest.mark.parametrize("cutoff", [0.01, 0.025, 0.2])
def test_constant_stopping_has_positive_subfloor_loss(cutoff: float) -> None:
    # For constant restricted stopping S, E(R)=ECUT+S*R exactly.
    stopping = 20.0
    ranges = np.geomspace(1.0e-5, 1.0, 2048)
    values = (cutoff + stopping * ranges)[None, :]
    log_min = math.log(float(ranges[0]))
    inv_dlog = 2047 / math.log(1.0e5)
    initial = float(values[0, 0])
    for fraction in [0.125, 0.5, 0.875]:
        residual = float(ranges[0]) * fraction
        actual = lookup_inverse_restricted_range(
            values, 0, log_min, inv_dlog, 2048, residual, cutoff
        )
        assert cutoff < actual < initial
        assert abs(actual - (cutoff + stopping * residual)) < 1.0e-15


def test_zero_residual_is_the_cutoff() -> None:
    values = np.array([[0.0102, 0.0104]])
    assert lookup_inverse_restricted_range(values, 0, math.log(1.0e-5), 1.0, 2, 0.0, 0.01) == 0.01


def test_ordinary_inverse_nodes_keep_the_existing_interpolation() -> None:
    ranges = np.geomspace(1.0e-5, 1.0, 2048)
    values = (0.01 + 20 * ranges)[None, :]
    log_min = math.log(1.0e-5)
    inv_dlog = 2047 / math.log(1.0e5)
    for residual in np.geomspace(1.0e-5, 1.0, 97):
        expected = lookup_loglinear_2d(values, 0, log_min, inv_dlog, 2048, float(residual))
        actual = lookup_inverse_restricted_range(
            values, 0, log_min, inv_dlog, 2048, float(residual), 0.01
        )
        assert abs(actual - expected) < 1.0e-14
