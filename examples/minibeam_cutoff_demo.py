"""Measure electron-cutoff effects in a spectral 0.5 mm field through a density slab.

Run ``python -m examples.minibeam_cutoff_demo --device cuda:0`` from the repository
root. Saves a profile figure beside this script. The old 200 keV cutoff and a
50 keV instrument are compared with the current default, using paired independent
batches. This demonstrates a cutoff effect, not absolute validation of the
analytic material model or a physical brass collimator. No external data needed.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt

from pyradmc import ECUT_MEV, AnalyticCrossSections, VoxelGrid
from pyradmc.backends.warp.engine import WarpEngine
from pyradmc.data.materials import WATER
from pyradmc.geometry.source import SpectralBeamSource
from pyradmc.geometry.spectrum import ali_rogers_mv
from pyradmc.scoring.grid import ScoringGrid


@dataclass
class CutoffComparison:
    """Per-batch water profiles and central energy fractions, never voxel sigma sums."""

    x_cm: npt.NDArray[np.float64]
    profiles: dict[float, npt.NDArray[np.float64]]
    central_fractions: dict[float, npt.NDArray[np.float64]]


def compare_cutoffs(
    device: str, n_histories: int = 400_000, n_batches: int = 8
) -> CutoffComparison:
    """Use a 6 MV point source and a 1 cm low-density slab upstream of the ROI.

    The slab has water composition at 0.25 g/cm3: a density-heterogeneity
    instrument, not a commissioned lung material. Counts are per cutoff, split
    into independent batches. Seeds are paired across
    cutoffs, not counted as extra independent source photons. The ROI is water at
    depth 2-4 cm, integrated over the full y extent. All dose is per emitted photon.
    """
    if n_batches < 2 or n_histories % n_batches:
        raise ValueError("need at least two equal, independent batches")
    shape = (401, 2, 60)
    density = np.ones(shape)
    material = np.full(shape, WATER, dtype=np.int32)
    density[:, :, 10:20] = 0.25
    grid = VoxelGrid(
        shape=shape,
        spacing=(0.01, 1.0, 0.1),
        origin=(-2.005, -1.0, 0.0),
        density=density,
        material=material,
    )
    scorer = ScoringGrid.rebin(
        grid, shape=(401, 1, 60), spacing=(0.01, 2.0, 0.1), origin=grid.origin
    )
    xs = AnalyticCrossSections(geometry_densities=grid.max_density_by_material())
    engine = WarpEngine(grid=grid, cross_sections=xs, device=device)
    source = SpectralBeamSource(
        spectrum=ali_rogers_mv("varian-6mv"),
        focal_point=(0.0, 0.0, -100.0),
        center=(0.0, 0.0, 0.0),
        width_u=0.05,
        width_v=1.0,
    )
    x = -2.005 + (np.arange(shape[0]) + 0.5) * 0.01
    central = np.abs(x) < 0.025
    profiles: dict[float, npt.NDArray[np.float64]] = {}
    fractions: dict[float, npt.NDArray[np.float64]] = {}
    for cut in dict.fromkeys([0.2, 0.05, ECUT_MEV]):
        runs = []
        for batch in range(n_batches):
            result = engine.run(
                source,
                n_histories=n_histories // n_batches,
                n_batches=1,
                seed=2510031 + 113 * batch,
                scoring_grid=scorer,
                ecut=cut,
            )
            runs.append(result.dose[:, 0, 20:40].mean(axis=1))
        profiles[cut] = np.asarray(runs)
        fractions[cut] = profiles[cut][:, central].sum(axis=1) / profiles[cut].sum(axis=1)
    return CutoffComparison(x, profiles, fractions)


def main() -> None:
    """Plot absolute profiles with independent-batch SEM and print central fractions."""
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--histories", type=int, default=400_000)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_suffix(".png"))
    args = parser.parse_args()
    comparison = compare_cutoffs(args.device, args.histories)
    fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
    for cut, profiles in comparison.profiles.items():
        mean = profiles.mean(axis=0)
        sem = profiles.std(axis=0, ddof=1) / np.sqrt(len(profiles))
        label = f"{cut * 1000:g} keV" + (" (default)" if cut == ECUT_MEV else "")
        ax.plot(comparison.x_cm * 10, mean, label=label)
        ax.fill_between(comparison.x_cm * 10, mean - sem, mean + sem, alpha=0.15)
        values = comparison.central_fractions[cut]
        print(
            f"{label}: central fraction {values.mean():.4f} ± "
            f"{values.std(ddof=1) / np.sqrt(len(values)):.4f} SEM"
        )
    ax.set(
        xlim=(-2, 2),
        xlabel="x (mm)",
        ylabel="Dose (MeV/g / incident photon)",
        title=(
            "0.5 mm spectral field through density slab | water depth 2-4 cm\n"
            "Full-y average; ±1 SEM"
        ),
    )
    ax.legend(frameon=False)
    ax.grid(alpha=0.2)
    fig.savefig(args.output, dpi=160)
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
