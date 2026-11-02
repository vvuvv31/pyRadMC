"""Score directly in a placed native voxel grid, without dose interpolation.

Run ``python -m examples.oriented_scoring_demo``; saves a native-plane dose figure
beside this script. The transport phantom remains an axis-aligned water box.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from pyradmc.backends.warp.engine import WarpEngine
from pyradmc.data.analytic import AnalyticCrossSections
from pyradmc.geometry.grid import VoxelGrid
from pyradmc.geometry.source import PencilBeamSource
from pyradmc.scoring.grid import OrientedScoringGrid


def main() -> None:
    """Transport a small pencil field and plot dose in native scoring coordinates."""
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    phantom = VoxelGrid.uniform_water((16, 16, 24), (0.5, 0.5, 0.5))
    angle = np.deg2rad(24)
    c, s = np.cos(angle), np.sin(angle)
    score = OrientedScoringGrid(
        shape=(8, 8, 8),
        origin=(-2.0, -2.0, -2.0),
        spacing=(0.5, 0.5, 0.5),
        voxel_mass=np.full((8, 8, 8), 0.125),
        rotation=np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]),
        translation=np.array([4.0, 4.0, 6.0]),
    )
    result = WarpEngine(
        grid=phantom,
        cross_sections=AnalyticCrossSections(geometry_densities=phantom.max_density_by_material()),
        device=args.device,
    ).run(
        PencilBeamSource(6.0, (4.0, 4.0, -1.0), (0.0, 0.0, 1.0)),
        n_histories=16_000,
        n_batches=8,
        seed=817,
        scoring_grid=score,
    )
    fig, ax = plt.subplots(figsize=(6, 5), layout="constrained")
    image = ax.imshow(
        result.dose.mean(axis=1).T * 1.602176634e5,
        origin="lower",
        extent=(-2, 2, -2, 2),
        cmap="inferno",
    )
    ax.set(xlabel="Native x [cm]", ylabel="Native z [cm]", title="24° native scoring placement")
    fig.colorbar(image, ax=ax, label="μGy / 1e9 photons (native-y mean)")
    fig.savefig(Path(__file__).with_suffix(".png"), dpi=150)


if __name__ == "__main__":
    main()
