"""Sparse angular data must preserve Coulomb transport scaling between nodes."""

from __future__ import annotations

import numpy as np

from pyradmc.data.materials import AVOGADRO, STANDARD_ATOMIC_WEIGHT
from pyradmc.data.tabulated.eedl import element_scattering_power
from tests.unit.test_eedl import _ang_525, _xs_525


def test_sparse_shapes_preserve_analytic_reduced_transport() -> None:
    """For sigma_1(E)=C/(p*beta)^2, a sparse shape grid is sufficient.

    Total elastic sigma is independently tabulated on a dense grid. Its
    curvature need not match sigma_1: the normalized angular mean carries
    their ratio, not a universal power law in energy. Synthetic uniform-band
    angular distributions have exactly known first moments0.1 and0.001.
    ENDF synthetic cross sections retain six significant figures, hence2e-5.
    """
    mev = np.array([0.256, 1.0, 3.0, 10.0])
    mass = 0.51099895
    factor = (mev * (mev + 2 * mass) / (mev + mass)) ** 2
    constant = 100 * factor[0] * 0.1
    sigma = np.array([100.0, 70.0, 40.0, constant / (factor[-1] * 0.001)])
    text = "\n".join(
        _xs_525(800, (mev * 1e6).tolist(), sigma.tolist())
        + _ang_525(
            800,
            [
                (256000.0, [0.800001, 0.999999], [1.0, 1.0]),
                (10000000.0, [0.998001, 0.999999], [1.0, 1.0]),
            ],
        )
    )
    energies, actual = element_scattering_power(text, elements={8})[8]
    np.testing.assert_allclose(energies, mev, rtol=1e-6)
    expected = 2 * AVOGADRO / STANDARD_ATOMIC_WEIGHT[8] * constant / factor * 1e-24
    np.testing.assert_allclose(actual, expected, rtol=2e-5)
