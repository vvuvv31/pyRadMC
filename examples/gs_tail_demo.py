"""Show how GS table compression represents rare electron scattering angles.

Run ``python -m examples.gs_tail_demo`` to save a figure beside this script.
This isolated electron-step distribution is not a dose-validation result. The
uncompressed GS construction is shared by both table representations; changing
CDF cells neither fits scattering strength nor changes the underlying law.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from pyradmc.data.goudsmit_saunderson import _gs_raw_cosines, gs_scaled_deflection_table


def main() -> None:
    """Compare angular survival curves and the second transport moment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_suffix(".png"))
    args = parser.parse_args()
    eta, theta2, count = 1e-4, 0.01, 512
    raw = _gs_raw_cosines(eta, theta2, 4096)
    y = 1 - raw
    anchor = -np.expm1(-theta2 / 2)
    old = y.reshape(count, -1).mean(axis=1) / y.mean()
    current = gs_scaled_deflection_table(eta, theta2, n_u=count)
    edges = np.expm1(np.arange(count + 1) * 10 / count) / np.expm1(10)
    laws = [
        ("Uncompressed construction", y / y.mean(), np.full(len(y), 1 / len(y))),
        ("Historical: 512 equal-probability cells", old, np.full(count, 1 / count)),
        ("Current: 512 logarithmic-probability cells", current, np.diff(edges)),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    moments = []
    for label, w, probability in laws:
        mu = np.maximum(-1, 1 - w * anchor)
        angle = np.degrees(np.arccos(mu))
        axes[0].loglog(angle, np.cumsum(probability), label=label)
        moments.append(float(probability @ (1 - (3 * mu**2 - 1) / 2)))
    axes[0].set(xlabel="Electron deflection angle (degrees)", ylabel="Probability of larger angle")
    axes[0].legend(fontsize=7)
    axes[0].grid(alpha=0.25, which="both")
    ratios = np.array(moments) / moments[0]
    axes[1].bar(["Raw", "Equal cells", "Log cells"], ratios, color=["C0", "C1", "C2"])
    axes[1].axhline(1, color="black", linewidth=0.8)
    axes[1].set(
        ylabel="Second transport moment / raw construction",
        ylim=(min(0.99, float(ratios.min()) - 0.01), max(1.01, float(ratios.max()) + 0.01)),
    )
    fig.suptitle(
        r"Same GS law and first-moment anchor: $\eta=10^{-4}$, $\langle\theta^2\rangle=0.01$"
    )
    fig.savefig(args.output, dpi=160)
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
