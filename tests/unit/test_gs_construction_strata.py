"""Build-time variance control must preserve single-scatter CDF coverage."""

from __future__ import annotations

from unittest.mock import Mock

import numpy as np

from pyradmc.data.goudsmit_saunderson import _mc_gs_cosines


def test_single_collision_covers_each_inverse_cdf_stratum_once() -> None:
    """With multiplicity fixed to one, the finite table covers all CDF strata.

    This deterministic construction property is independent of a dose reference.
    It changes neither the Poisson collision law in production nor the marginal
    single-scatter distribution. No statistical acceptance threshold is used.
    """
    n = 4096
    eta = 0.03
    rng = Mock(wraps=np.random.default_rng(20261103))
    rng.poisson.return_value = np.ones(n, dtype=np.int64)
    mu = _mc_gs_cosines(eta, 1.0, n, rng)
    # Independent forward CDF of the screened Rutherford distribution.
    xi = eta * (1.0 + mu) / (1.0 + 2.0 * eta - mu)
    cells = np.floor(xi * n).astype(np.int64)
    np.testing.assert_array_equal(np.sort(cells), np.arange(n))


def test_construction_is_reproducible_for_fixed_seed() -> None:
    """The host table builder has one fixed target and must repeat exactly."""
    a = _mc_gs_cosines(1e-4, 8.0, 4096, np.random.default_rng(20261103))
    b = _mc_gs_cosines(1e-4, 8.0, 4096, np.random.default_rng(20261103))
    np.testing.assert_array_equal(a, b)
