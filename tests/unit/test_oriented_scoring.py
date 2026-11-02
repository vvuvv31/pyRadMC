"""Rigid scoring transforms preserve native CT voxel indices and mass."""

import numpy as np
import pytest

from pyradmc.scoring.grid import OrientedScoringGrid


def test_rotated_translated_grid_native_indices():
    rotation = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]])
    grid = OrientedScoringGrid(
        shape=(2, 3, 4),
        spacing=(1.0, 1.0, 1.0),
        origin=(-1.0, -1.0, -1.0),
        voxel_mass=np.ones((2, 3, 4)),
        rotation=rotation,
        translation=np.array([10.0, 20.0, 30.0]),
    )
    for index in np.ndindex(grid.shape):
        local = np.asarray(grid.origin) + np.asarray(index) + 0.5
        world = rotation @ local + grid.translation
        assert grid.flat_index(*world) == np.ravel_multi_index(index, grid.shape)
    assert grid.flat_index(*(rotation @ np.array([1.1, 0.0, 0.0]) + grid.translation)) == -1
    with pytest.raises(ValueError, match="rotation"):
        OrientedScoringGrid(
            shape=(1, 1, 1),
            spacing=(1.0, 1.0, 1.0),
            origin=(0.0, 0.0, 0.0),
            voxel_mass=np.ones((1, 1, 1)),
            rotation=2 * rotation,
            translation=np.zeros(3),
        )
