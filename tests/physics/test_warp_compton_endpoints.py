"""Float32 kinematic endpoints must never create negative recoil or terminal energy."""

from __future__ import annotations

import sys

import numpy as np
import pytest

wp = pytest.importorskip("warp")
pytestmark = [pytest.mark.warp, pytest.mark.gpu]


def test_fast_math_compton_recoil_is_nonnegative() -> None:
    if not wp.is_cuda_available():
        pytest.skip("CUDA float32 fast-math endpoint regression")
    from pyradmc.backends.warp.physics import warp_physics
    from pyradmc.rng.warp_shim import WarpRNGState, init_slot, uniform

    sample = warp_physics().sample_compton_energy_ratio

    @wp.kernel
    def probe(slots: wp.array(dtype=wp.uint32), maxima: wp.array(dtype=float)):
        tid = wp.tid()
        slots[tid] = init_slot(20260711, tid)
        state = WarpRNGState()
        state.slots = slots
        state.idx = tid
        maximum = float(0.0)  # noqa: UP018 - Warp mutable loop variable
        for _ in range(128):
            energy = 0.05 + 6.0 * uniform(state)
            maximum = wp.max(maximum, sample(energy, state))
        maxima[tid] = maximum

    wp.set_module_options({"fast_math": True}, module=sys.modules[__name__])
    n = 1_000_000
    slots = wp.zeros(n, dtype=wp.uint32, device="cuda:0")
    maxima = wp.zeros(n, dtype=float, device="cuda:0")
    wp.launch(probe, dim=n, inputs=[slots, maxima], device="cuda:0")
    values = maxima.numpy()
    assert np.all(values <= 1.0), (
        f"{np.count_nonzero(values > 1)} streams gained photon energy; "
        f"largest E'/E = {values.max():.9g}"
    )


@pytest.mark.warp
@pytest.mark.gpu
def test_cuda_capped_brems_budget_is_nonnegative() -> None:
    if not wp.is_cuda_available():
        pytest.skip("CUDA endpoint regression")
    from pyradmc.backends.warp.physics import warp_physics

    budget = warp_physics().capped_bremsstrahlung_budget

    @wp.kernel
    def probe(inputs: wp.array(dtype=float), output: wp.array(dtype=float)):
        photon, remaining = budget(inputs[0], inputs[1], inputs[0])
        output[0] = photon
        output[1] = remaining

    inputs = wp.array([0.8, 0.0393973775208], dtype=float, device="cuda:0")
    output = wp.zeros(2, dtype=float, device="cuda:0")
    wp.launch(probe, dim=1, inputs=[inputs, output], device="cuda:0")
    values = output.numpy()
    assert np.all(values >= 0)
    assert float(values.sum() + inputs.numpy()[1]) == pytest.approx(0.8, abs=1e-7)
