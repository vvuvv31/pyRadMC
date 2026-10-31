"""A capped radiative event cannot spend energy reserved for the second half-step."""

from __future__ import annotations

import numpy as np
import pytest


def test_brems_cap_preserves_nonnegative_terminal_energy() -> None:
    from pyradmc.physics.brems import capped_bremsstrahlung_budget

    # Captured CUDA reserve: a representative capped event loses 1.86e-8 MeV.
    # The reserve is continuous energy already scheduled for the second segment.
    energy = np.float32(0.8)
    reserved = np.float32(0.0393973775208)
    legacy_remaining = (energy - min(energy, energy - reserved)) - reserved
    assert legacy_remaining < 0  # The unprojected float32 budget is invalid.
    photon, remaining = capped_bremsstrahlung_budget(energy, reserved, energy)
    assert photon >= 0
    assert remaining >= 0
    assert float(photon + reserved + remaining) == pytest.approx(float(energy), abs=1e-7)


def test_uncapped_brems_budget_conserves_energy() -> None:
    from pyradmc.physics.brems import capped_bremsstrahlung_budget

    photon, remaining = capped_bremsstrahlung_budget(1.0, 0.1, 0.3)
    assert photon == 0.3
    assert photon + remaining + 0.1 == pytest.approx(1.0)
