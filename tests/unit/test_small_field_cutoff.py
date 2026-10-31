"""Residual electron range must fit below the validated small-field scale.

The default local-energy termination must not suppress transport over a whole
0.5 mm aperture. The 0.1 mm scoring study assigns at most a quarter-bin (25 um)
CSDA path to local termination in water; lateral displacement cannot exceed this
path. Spectral brass/water measurements and their remaining limitations are in
``docs/minibeam.md``. This is a physical range budget, not a literal cutoff pin.
"""

from pyradmc import ECUT_MEV
from pyradmc.data.analytic import AnalyticCrossSections
from pyradmc.data.materials import MATERIALS, WATER


def test_default_residual_electron_range_is_sub_bin() -> None:
    xs = AnalyticCrossSections()
    residual_path_cm = xs.csda_range(ECUT_MEV, WATER) / MATERIALS[WATER].density
    scoring_bin_cm = 0.01
    assert residual_path_cm <= 0.25 * scoring_bin_cm, (
        f"default local termination suppresses {residual_path_cm * 10:.3f} mm "
        "of water CSDA path on a 0.1 mm scoring grid"
    )
