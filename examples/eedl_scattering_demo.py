"""Plot the effect of sparse EEDL angular-data interpolation.

Run ``python -m examples.eedl_scattering_demo --eedl /path/to/EEDL2023.ALL``.
The default uses the existing EPICS cache; no library is downloaded. The PNG
is written beside this script. Runtime is a few seconds on a CPU.

This plots nuclear elastic scattering data, not dose. The current curve includes
reduced-transport interpolation and exact linear-PDF product integration. The
historical curve reconstructs both former approximations for this figure only.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

from pyradmc.data.materials import AVOGADRO, STANDARD_ATOMIC_WEIGHT
from pyradmc.data.tabulated.build import library_path
from pyradmc.data.tabulated.eedl import element_scattering_power, material_scattering_power
from pyradmc.data.tabulated.endf import read_mf26_angular_distributions, read_tab1_by_mf
from pyradmc.data.tabulated.epdl import mass_fractions_from_formula


def historical_tables(
    text: str, elements: set[int]
) -> dict[int, tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]]:
    """Reconstruct the old normalized-moment interpolation for this figure only."""
    sections = read_tab1_by_mf(text, 23)
    shapes = read_mf26_angular_distributions(text, 525)
    result = {}
    for z in elements:
        energies, sigma = sections[(100 * z, 525)]
        entries = shapes[100 * z]
        shape_energies = np.array([e for e, _, _ in entries])
        means = np.array(
            [np.trapezoid((1 - mu) * p, mu) / np.trapezoid(p, mu) for _, mu, p in entries]
        )
        mean = np.exp(np.interp(np.log(energies), np.log(shape_energies), np.log(means)))
        power = 2 * AVOGADRO / STANDARD_ATOMIC_WEIGHT[z] * sigma * 1e-24 * mean
        result[z] = (energies * 1e-6, power)
    return result


def main() -> None:
    """Read an existing EEDL file and save the comparison figure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eedl", type=Path, default=library_path("eedl"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_suffix(".png"))
    args = parser.parse_args()
    if not args.eedl.is_file():
        parser.error(f"EEDL file missing: {args.eedl}; supply --eedl with an existing library")
    text = args.eedl.read_text(encoding="latin-1")
    elements = {1, 8, 74}
    current = element_scattering_power(text, elements)
    historical = historical_tables(text, elements)
    energies = np.geomspace(0.025, 20.0, 512)
    mixtures = [("Water", mass_fractions_from_formula({1: 2, 8: 1})), ("Tungsten", {74: 1.0})]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), constrained_layout=True)
    for column, (name, fractions) in enumerate(mixtures):
        old = material_scattering_power(historical, fractions, energies)
        new = material_scattering_power(current, fractions, energies)
        ax = axes[0, column]
        ax.loglog(energies, old, label="Historical: interpolate normalized moment")
        ax.loglog(energies, new, label="Reduced transport + exact angular integral")
        ax.set(title=name, ylabel="Nuclear scattering power (rad² cm²/g)")
        ax.legend(fontsize=8)
        axes[1, column].semilogx(energies, old / new)
        axes[1, column].axhline(1, color="black", linewidth=0.7)
        axes[1, column].set(xlabel="Electron kinetic energy (MeV)", ylabel="Historical / current")
        for row in range(2):
            axes[row, column].axvspan(0.256, 10, alpha=0.1, color="gray")
            axes[row, column].grid(alpha=0.25, which="both")
    fig.suptitle(
        "EEDL sparse angular data: shaded 0.256-10 MeV gap\nNo dose fitting; nuclear component only"
    )
    fig.savefig(args.output, dpi=160)
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
