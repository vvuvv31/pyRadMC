"""Voxelize seven circular holes and transport a spectral photon field through them.

Run ``python -m examples.hexagonal_holes_demo --tables materials.npz --device cuda:0``. The default
uses 2 mm holes, 4 mm pitch and 0.1 mm transverse voxels. Saves geometry,
dose maps and a central profile beside this script. Tungsten from the shipped
material registry uses precompiled tabulated data at the default cutoff;
it does not validate brass data, true circular walls, or clinical dose accuracy.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from pyradmc import VoxelGrid
from pyradmc.backends.warp.engine import WarpEngine
from pyradmc.data.materials import AIR, MATERIALS, TUNGSTEN, WATER
from pyradmc.data.tabulated.format import load_tables
from pyradmc.data.tabulated.source import TabulatedCrossSections
from pyradmc.geometry.holes import HexagonalHoleCollimator
from pyradmc.geometry.source import SpectralBeamSource
from pyradmc.geometry.spectrum import ali_rogers_mv
from pyradmc.scoring.grid import ScoringGrid


def main() -> None:
    """Save an explicit aperture and depth-resolved dose with batch uncertainty."""
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument(
        "--tables",
        type=Path,
        required=True,
        help="precompiled registry NPZ at the current ECUT (including tungsten)",
    )
    parser.add_argument("--histories", type=int, default=4_000_000)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_suffix(".png"))
    args = parser.parse_args()
    if args.histories < 8 or args.histories % 8:
        parser.error("histories must be a positive multiple of eight")
    shape = (400, 400, 60)
    density = np.ones(shape, dtype=np.float32)
    material = np.full(shape, WATER, dtype=np.uint8)
    density[:, :, :20] = MATERIALS[AIR].density
    material[:, :, :20] = AIR
    grid = VoxelGrid(shape, (0.01, 0.01, 0.2), density, material, (-2, -2, -4))
    holes = HexagonalHoleCollimator(0.2, 0.4, 1, (-3, -1))
    holes.paint(grid, solid_material=TUNGSTEN, solid_density=MATERIALS[TUNGSTEN].density)
    scoring = ScoringGrid(
        shape=(160, 160, 40),
        spacing=(0.01, 0.01, 0.2),
        origin=(-0.8, -0.8, 0),
        voxel_mass=np.full((160, 160, 40), 0.00002),
    )
    source = SpectralBeamSource(
        spectrum=ali_rogers_mv("varian-6mv"),
        focal_point=(0, 0, -100),
        center=(0, 0, 0),
        width_u=2,
        width_v=2,
    )
    xs = TabulatedCrossSections(
        load_tables(args.tables), geometry_densities=grid.max_density_by_material()
    )
    engine = WarpEngine(grid=grid, cross_sections=xs, device=args.device)
    batches = []
    for batch in range(8):
        result = engine.run(
            source,
            n_histories=args.histories // 8,
            n_batches=1,
            seed=60110031 + 137 * batch,
            scoring_grid=scoring,
        )
        batches.append(result.dose)
    dose = np.asarray(batches)
    x = -0.8 + (np.arange(160) + 0.5) * 0.01
    mean = dose.mean(axis=0)
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), layout="constrained")
    mask = holes.aperture_mask(x, x)
    axes[0, 0].imshow(
        mask.T, origin="lower", extent=(-8, 8, -8, 8), interpolation="nearest", cmap="gray"
    )
    axes[0, 0].set(title="Seven holes: 2 mm diameter / 4 mm pitch")
    scale = 1.602176634e5  # MeV/g/photon -> microGy per 1e9 upstream photons
    for ax, (lo, hi) in zip(axes.flat[1:5], [(0, 5), (5, 10), (15, 20), (30, 35)], strict=True):
        image = ax.imshow(
            mean[:, :, lo:hi].mean(axis=2).T * scale,
            origin="lower",
            extent=(-8, 8, -8, 8),
            interpolation="nearest",
            cmap="inferno",
        )
        ax.set(title=f"Water depth {lo * 0.2:g}-{hi * 0.2:g} cm")
        fig.colorbar(image, ax=ax, label="μGy / 1e9 upstream photons", shrink=0.75)
    # Integrate a 0.8 mm central-y band and 2 cm depth inside every batch.
    profiles = dose[:, :, abs(x) < 0.04, 10:20].mean(axis=(2, 3))
    profile = profiles.mean(axis=0)
    sem = profiles.std(axis=0, ddof=1) / np.sqrt(len(profiles))
    axes[1, 2].plot(x * 10, profile * scale)
    axes[1, 2].fill_between(x * 10, (profile - sem) * scale, (profile + sem) * scale, alpha=0.2)
    axes[1, 2].set(
        title="Depth 2-4 cm / central y band / ±1 SEM",
        xlabel="x (mm)",
        ylabel="μGy / 1e9 upstream photons",
    )
    for ax in axes.flat[:5]:
        ax.set(xlabel="x (mm)", ylabel="y (mm)")
    fig.suptitle("Explicit voxelized tungsten / air; 0.1 mm XY grid; absolute dose")
    fig.savefig(args.output, dpi=160)
    print(f"Saved {args.output}; {args.histories} photons in eight independent batches")


if __name__ == "__main__":
    main()
