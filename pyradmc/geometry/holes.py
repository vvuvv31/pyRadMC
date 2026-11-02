"""Circular-hole arrays painted into rectilinear material grids.

This host-side geometry builder adds no transport surfaces or attenuation mask.
Both photon and electron transport see the same explicit solid/opening voxels.
Lengths are in cm. The holes are straight and parallel to the grid z axis;
they are not focused toward a divergent source.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from pyradmc.data import materials
from pyradmc.geometry.grid import VoxelGrid

__all__ = ["HexagonalHoleCollimator"]


@dataclass(frozen=True)
class HexagonalHoleCollimator:
    """Finite hexagonal array of circular holes in a full-transverse solid slab.

    The centers follow ``x = pitch*(q+r/2), y = pitch*sqrt(3)*r/2`` for
    ``max(abs(q),abs(r),abs(q+r)) <= rings``, giving ``1+3*rings*(rings+1)``
    holes. Ring zero is a single central hole; ring one contains seven holes.
    ``center_cm`` translates the array. All lengths, including ``z_range_cm``,
    are physical grid-frame coordinates, not projected isocenter settings.

    Rasterization assigns a whole cell by its transverse center: strictly
    ``(x-cx)^2+(y-cy)^2 < (diameter/2)^2``. Curved walls therefore become
    staircases, and nominal area, width and sixfold symmetry need not survive
    a Cartesian grid. There are no fractional-density edge cells. Report the
    actual rasterized area and retain this geometry error in dose comparisons.
    Slab faces must align with z voxel faces; holes must fit inside x/y bounds.
    """

    diameter_cm: float
    pitch_cm: float
    rings: int
    z_range_cm: tuple[float, float]
    center_cm: tuple[float, float] = (0.0, 0.0)

    def __post_init__(self) -> None:
        """Reject nonphysical dimensions before any material grid is changed."""
        if (
            not isinstance(self.rings, (int, np.integer))
            or isinstance(self.rings, bool)
            or self.rings < 0
        ):
            raise ValueError("rings must be a nonnegative integer")
        dimensions = (self.diameter_cm, self.pitch_cm, *self.z_range_cm, *self.center_cm)
        if not all(math.isfinite(v) for v in dimensions):
            raise ValueError("hole dimensions and positions must be finite")
        if self.diameter_cm <= 0 or self.pitch_cm < self.diameter_cm:
            raise ValueError("require positive diameter and pitch >= diameter")
        if self.z_range_cm[0] >= self.z_range_cm[1]:
            raise ValueError("z_range_cm must have positive thickness")

    @property
    def centers_cm(self) -> NDArray[np.float64]:
        """Return physical (x,y) hole centers, ordered by integer axial coordinates."""
        n = self.rings
        return np.array(
            [
                (
                    self.center_cm[0] + self.pitch_cm * (q + r / 2),
                    self.center_cm[1] + self.pitch_cm * math.sqrt(3) * r / 2,
                )
                for q in range(-n, n + 1)
                for r in range(-n, n + 1)
                if max(abs(q), abs(r), abs(q + r)) <= n
            ],
            dtype=np.float64,
        )

    def aperture_mask(self, x_cm: ArrayLike, y_cm: ArrayLike) -> NDArray[np.bool_]:
        """Classify cell centers; return an (nx,ny) Boolean opening mask."""
        x, y = np.asarray(x_cm, dtype=np.float64), np.asarray(y_cm, dtype=np.float64)
        if x.ndim != 1 or y.ndim != 1 or not x.size or not y.size:
            raise ValueError("x_cm and y_cm must be nonempty one-dimensional arrays")
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("cell centers must be finite")
        mask = np.zeros((len(x), len(y)), dtype=bool)
        for cx, cy in self.centers_cm:
            mask |= (x[:, None] - cx) ** 2 + (y[None, :] - cy) ** 2 < (self.diameter_cm / 2) ** 2
        return mask

    def paint(
        self,
        grid: VoxelGrid,
        *,
        solid_material: int,
        solid_density: float,
        opening_material: int = materials.AIR,
        opening_density: float | None = None,
    ) -> None:
        """Overwrite the aligned slab in place, preserving all other voxel values.

        Supply a material supported by the chosen cross-section source. No alloy
        is registered here; brass data remain a separate material concern.
        Openings default to registry air density. Both opening and solid density
        are actual g/cm3, not volume fractions. All validation precedes mutation.
        """
        if opening_density is None:
            opening_density = materials.MATERIALS[materials.AIR].density
        for index in (solid_material, opening_material):
            if not isinstance(index, (int, np.integer)) or not 0 <= index < len(
                materials.MATERIALS
            ):
                raise ValueError("material index outside the registry")
        for density in (solid_density, opening_density):
            if not math.isfinite(density) or density <= 0:
                raise ValueError("material densities must be finite and positive")
        if grid.material.dtype.kind not in "iu" or grid.density.dtype.kind != "f":
            raise ValueError("paint requires integer material and floating density arrays")
        if not grid.material.flags.writeable or not grid.density.flags.writeable:
            raise ValueError("paint requires writable arrays")
        if max(solid_material, opening_material) > np.iinfo(grid.material.dtype).max:
            raise ValueError("material index does not fit the grid dtype")
        if max(solid_density, opening_density) > np.finfo(grid.density.dtype).max:
            raise ValueError("density does not fit the grid dtype")
        lower, upper = self.z_range_cm
        indices = [(z - grid.origin[2]) / grid.spacing[2] for z in (lower, upper)]
        if any(abs(i - round(i)) > 1e-8 for i in indices):
            raise ValueError("collimator slab faces must align with z voxel faces")
        start, stop = (round(i) for i in indices)
        if start < 0 or stop > grid.shape[2]:
            raise ValueError("collimator slab is outside the grid")
        radius = self.diameter_cm / 2
        centers = self.centers_cm
        for axis in (0, 1):
            if (
                centers[:, axis].min() - radius < grid.origin[axis] - 1e-12
                or centers[:, axis].max() + radius > grid.upper_corner[axis] + 1e-12
            ):
                raise ValueError("nominal holes must fit within the transverse grid")
        x = grid.origin[0] + (np.arange(grid.shape[0]) + 0.5) * grid.spacing[0]
        y = grid.origin[1] + (np.arange(grid.shape[1]) + 0.5) * grid.spacing[1]
        mask = self.aperture_mask(x, y)
        if not mask.any():
            raise ValueError("grid resolves no opening cells")
        grid.material[:, :, start:stop] = np.where(mask, opening_material, solid_material)[
            :, :, None
        ]
        grid.density[:, :, start:stop] = np.where(mask, opening_density, solid_density)[:, :, None]
