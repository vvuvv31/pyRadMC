"""Compiled inverse-range endpoint against a constant-stopping oracle."""

from __future__ import annotations

import math

import numpy as np
import pytest

wp = pytest.importorskip("warp")
pytestmark = pytest.mark.warp


@pytest.mark.parametrize("device", ["cpu", pytest.param("cuda:0", marks=pytest.mark.gpu)])
def test_inverse_endpoint_on_device(device: str) -> None:
    if device.startswith("cuda") and not wp.is_cuda_available():
        pytest.skip("no CUDA device")
    from pyradmc.backends.warp.physics import warp_physics

    lookup = warp_physics().lookup_inverse_restricted_range

    @wp.kernel
    def probe(
        values: wp.array2d(dtype=float),
        remaining: wp.array(dtype=float),
        result: wp.array(dtype=float),
    ):
        i = wp.tid()
        result[i] = lookup(
            values, 0, math.log(1.0e-5), 2047.0 / math.log(1.0e5), 2048, remaining[i], 0.01
        )

    ranges = np.geomspace(1.0e-5, 1.0, 2048)
    values = wp.array((0.01 + 20 * ranges)[None, :].astype(np.float32), device=device)
    residuals = np.linspace(0.0, 1.0e-5, 101).astype(np.float32)
    remaining = wp.array(residuals, device=device)
    result = wp.zeros(len(residuals), dtype=float, device=device)
    wp.launch(probe, dim=len(residuals), inputs=[values, remaining, result], device=device)
    actual = result.numpy()
    assert np.all(np.diff(actual) > 0.0)
    assert actual[0] == np.float32(0.01)
    assert np.max(abs(actual - (0.01 + 20 * residuals))) < 3.0e-9
