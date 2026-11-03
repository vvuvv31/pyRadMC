"""GS probability bins must retain the rare-angle transport moments."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest


def test_probability_index_selects_logarithmic_intervals() -> None:
    from pyradmc.physics.gs import gs_probability_index

    n = 512
    edges = np.expm1(np.arange(n + 1) * 10.0 / n) / np.expm1(10.0)
    centers = (edges[:-1] + edges[1:]) / 2
    indices = [gs_probability_index(float(u), n) for u in centers]
    np.testing.assert_array_equal(indices, np.arange(n))
    assert gs_probability_index(0.0, n) == 0
    assert gs_probability_index(math.nextafter(1.0, 0.0), n) == n - 1


def test_compression_preserves_tail_second_moment(monkeypatch: pytest.MonkeyPatch) -> None:
    from pyradmc.data import goudsmit_saunderson as gs

    count = 1 << 19
    u = (np.arange(count) + 0.5) / count
    eta = 1e-5
    # Independent analytic inverse of screened Rutherford, widest angles first.
    y = 2 * eta * (1 - u) / (u + eta)
    monkeypatch.setattr(gs, "_node_cache", {})
    monkeypatch.setattr(gs, "_gs_raw_cosines", lambda *_: 1 - y)
    row = gs.gs_scaled_deflection_table(eta, 1e-3, n_u=512)
    edges = np.expm1(np.arange(513) * 10.0 / 512) / np.expm1(10.0)
    probabilities = np.diff(edges)
    # Analytic integration over the declared CDF cells, not stochastic draws.
    assert float(probabilities @ row) == pytest.approx(1.0, rel=1e-12)
    raw_second = float(np.mean((y / y.mean()) ** 2))
    compressed_second = float(probabilities @ row**2)
    assert abs(compressed_second / raw_second - 1) < 1e-3


def test_probability_map_is_part_of_cache_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pyradmc.data import goudsmit_saunderson as gs
    from pyradmc.data import interface

    before = gs._grid_cache_file(tmp_path)
    grid = gs.build_gs_grid(-12.0, -11.5, 2e-12, cache_dir=tmp_path)
    monkeypatch.setattr(interface, "_GS_PROBABILITY_LOG_SPAN", 9.0)
    monkeypatch.setattr(interface, "_GS_PROBABILITY_SCALE", math.expm1(9.0))
    assert gs._grid_cache_file(tmp_path) != before
    assert gs.build_gs_grid(-12.0, -11.5, 2e-12, cache_dir=tmp_path) is not grid
