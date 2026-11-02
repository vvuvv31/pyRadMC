"""Device binning of a native CT grid under exact rigid placement."""

from __future__ import annotations

import numpy as np
import pytest

wp = pytest.importorskip("warp")
from pyradmc.backends.warp import kernels  # noqa: E402
from pyradmc.backends.warp.engine import _scoring_info  # noqa: E402
from pyradmc.scoring.grid import OrientedScoringGrid  # noqa: E402

pytestmark = pytest.mark.warp


@wp.kernel
def _query(si: kernels.GridInfo, points: wp.array2d(dtype=float), out: wp.array(dtype=int)):
    i = wp.tid()
    out[i] = kernels._scoring_index(si, points[i, 0], points[i, 1], points[i, 2])


def test_world_positions_score_in_native_voxels() -> None:
    """Oblique placement preserves all native indices and excludes exterior points."""
    theta = 0.37
    c, s = np.cos(theta), np.sin(theta)
    rotation = np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])
    grid = OrientedScoringGrid(
        shape=(3, 4, 5),
        origin=(-1.0, -2.0, -3.0),
        spacing=(0.5, 0.75, 1.0),
        voxel_mass=np.ones((3, 4, 5)),
        rotation=rotation,
        translation=np.array([3.0, -4.0, 5.0]),
    )
    indices = np.array(list(np.ndindex(grid.shape)))
    local = np.asarray(grid.origin) + (indices + 0.5) * grid.spacing
    local = np.vstack((local, [-10.0, 0.0, 0.0]))
    points = (local @ rotation.T + grid.translation).astype(np.float32)
    out = wp.zeros(len(points), dtype=int, device="cpu")
    wp.launch(
        _query,
        dim=len(points),
        inputs=[_scoring_info(grid, "cpu"), wp.array(points, dtype=float, device="cpu"), out],
        device="cpu",
    )
    np.testing.assert_array_equal(out.numpy(), np.r_[np.arange(60), -1])


@wp.kernel
def _query_density(
    density: wp.array3d(dtype=float),
    material: wp.array3d(dtype=wp.uint8),
    out: wp.array(dtype=float),
):
    i = wp.tid()
    out[i] = kernels._density_at(density, material, i, 0, 0)


def test_material_density_storage_matches_voxel_storage() -> None:
    """A constant-per-material lookup changes storage without changing density."""
    material = wp.array(
        np.array([1, 0, 1], dtype=np.uint8).reshape(3, 1, 1), dtype=wp.uint8, device="cpu"
    )
    expected = np.array([8.55, 1.0, 8.55], dtype=np.float32)
    for values in (expected.reshape(3, 1, 1), np.array([1.0, 8.55]).reshape(1, 1, 2)):
        density = wp.array(values.astype(np.float32), dtype=float, device="cpu")
        out = wp.zeros(3, dtype=float, device="cpu")
        wp.launch(_query_density, dim=3, inputs=[density, material, out], device="cpu")
        np.testing.assert_array_equal(out.numpy(), expected)
