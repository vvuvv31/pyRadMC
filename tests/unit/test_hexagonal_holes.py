"""Hexagonal circular openings rasterized onto the shared transport voxel grid."""

import math

import numpy as np
import pytest

from pyradmc.data.materials import AIR, MATERIALS, TUNGSTEN, WATER
from pyradmc.geometry.grid import VoxelGrid
from pyradmc.geometry.holes import HexagonalHoleCollimator


@pytest.mark.parametrize(("rings", "count"), [(0, 1), (1, 7), (2, 19), (3, 37)])
def test_hexagonal_shell_count_pitch_and_inversion(rings: int, count: int) -> None:
    holes = HexagonalHoleCollimator(0.2, 0.4, rings, (-3.0, -1.0))
    centers = holes.centers_cm
    assert centers.shape == (count, 2)
    assert len(np.unique(centers, axis=0)) == count
    np.testing.assert_allclose(centers.mean(axis=0), 0.0, atol=1e-15)
    for center in centers:
        assert np.min(np.linalg.norm(centers + center, axis=1)) < 1e-15
    if rings:
        distances = np.linalg.norm(centers[:, None, :] - centers[None, :, :], axis=2)
        distances[distances == 0] = np.inf
        np.testing.assert_allclose(distances.min(axis=1), 0.4, atol=1e-15)


def test_two_mm_hole_on_point_one_mm_xy_grid() -> None:
    holes = HexagonalHoleCollimator(0.2, 0.4, 1, (-3.0, -1.0))
    x = -0.8 + (np.arange(160) + 0.5) * 0.01
    mask = holes.aperture_mask(x, x)
    xx, yy = np.meshgrid(x, x, indexing="ij")
    expected = np.zeros((160, 160), dtype=bool)
    for cx, cy in holes.centers_cm:
        expected |= (xx - cx) ** 2 + (yy - cy) ** 2 < 0.1**2
    np.testing.assert_array_equal(mask, expected)
    assert mask.dtype == np.bool_
    np.testing.assert_array_equal(mask, mask[::-1, ::-1])
    central = mask & (abs(xx) < 0.2) & (abs(yy) < 0.15)
    assert central.sum() == 316
    # This measures voxelization, not a tolerance on Monte Carlo dose.
    assert abs(central.sum() * 0.01**2 / (math.pi * 0.1**2) - 1) < 0.01


def test_paint_preserves_patient_and_air_outside_slab() -> None:
    grid = VoxelGrid.uniform_water((160, 160, 8), (0.01, 0.01, 0.5), (-0.8, -0.8, -3.0))
    before = grid.material.copy()
    holes = HexagonalHoleCollimator(0.2, 0.4, 1, (-3.0, -1.0))
    holes.paint(grid, solid_material=TUNGSTEN, solid_density=19.3)
    x = -0.8 + (np.arange(160) + 0.5) * 0.01
    mask = holes.aperture_mask(x, x)
    for iz in range(4):
        np.testing.assert_array_equal(grid.material[:, :, iz], np.where(mask, AIR, TUNGSTEN))
        np.testing.assert_array_equal(
            grid.density[:, :, iz], np.where(mask, MATERIALS[AIR].density, 19.3)
        )
    np.testing.assert_array_equal(grid.material[:, :, 4:], before[:, :, 4:])
    assert np.all(grid.density[:, :, 4:] == 1)
    assert grid.material[80, 80, 4] == WATER


@pytest.mark.parametrize("z_range", [(-3.1, -1.0), (-3.0, -0.9), (-4.0, -1.0)])
def test_non_aligned_or_outside_slab_rejected_without_mutation(
    z_range: tuple[float, float],
) -> None:
    grid = VoxelGrid.uniform_water((160, 160, 8), (0.01, 0.01, 0.5), (-0.8, -0.8, -3.0))
    holes = HexagonalHoleCollimator(0.2, 0.4, 1, z_range)
    with pytest.raises(ValueError):
        holes.paint(grid, solid_material=TUNGSTEN, solid_density=19.3)
    assert np.all(grid.material == WATER) and np.all(grid.density == 1)


@pytest.mark.parametrize(
    "diameter,pitch,rings,z_range",
    [
        (0, 0.4, 1, (-3, -1)),
        (0.2, 0.1, 1, (-3, -1)),
        (0.2, 0.4, -1, (-3, -1)),
        (0.2, 0.4, 1.5, (-3, -1)),
        (0.2, 0.4, 1, (-1, -3)),
        (float("nan"), 0.4, 1, (-3, -1)),
    ],
)
def test_invalid_array_parameters_rejected(diameter, pitch, rings, z_range) -> None:
    with pytest.raises(ValueError):
        HexagonalHoleCollimator(diameter, pitch, rings, z_range)


def test_translated_array_and_custom_opening_material() -> None:
    holes = HexagonalHoleCollimator(0.2, 0.4, 0, (-1.0, 0.0), center_cm=(0.1, -0.2))
    np.testing.assert_array_equal(holes.centers_cm, [[0.1, -0.2]])
    grid = VoxelGrid.uniform_water((40, 40, 4), (0.05, 0.05, 0.5), (-1, -1, -1))
    holes.paint(
        grid,
        solid_material=TUNGSTEN,
        solid_density=19.3,
        opening_material=WATER,
        opening_density=0.9,
    )
    assert grid.material[22, 16, 0] == WATER
    assert grid.density[22, 16, 0] == 0.9
