"""Measured default-cutoff effect in a spectral heterogeneous small field."""

from __future__ import annotations

import numpy as np
import pytest

from pyradmc import ECUT_MEV

pytestmark = [pytest.mark.validation, pytest.mark.warp, pytest.mark.gpu]


def test_default_retains_submillimetre_lateral_transport() -> None:
    wp = pytest.importorskip("warp")
    if not wp.is_cuda_available():
        pytest.skip("CUDA required for the measured spectral/density-slab cutoff study")
    from examples.minibeam_cutoff_demo import compare_cutoffs

    data = compare_cutoffs("cuda:0", n_histories=2_000_000)
    # Within each batch integrate first, then compare paired source histories.
    # The old high cutoff suppresses lateral transport and raises the fraction
    # of the dose confined to the 0.5 mm central band.
    difference = data.central_fractions[0.2] - data.central_fractions[ECUT_MEV]
    sem = difference.std(ddof=1) / np.sqrt(len(difference))
    assert difference.mean() > 3 * sem, (
        f"no resolved lateral-dose effect: paired central fraction change "
        f"{difference.mean():.5f} ± {sem:.5f} SEM"
    )
