# pyRadMC

[![PyPI version](https://img.shields.io/pypi/v/pyRadMC.svg)](https://pypi.org/project/pyRadMC/)
[![CI](https://github.com/e0404/pyRadMC/actions/workflows/ci.yml/badge.svg)](https://github.com/e0404/pyRadMC/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/e0404/pyRadMC/graph/badge.svg)](https://codecov.io/gh/e0404/pyRadMC)
[![Documentation](https://readthedocs.org/projects/pyradmc/badge/?version=latest)](https://pyradmc.readthedocs.io/en/latest/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

Fast photon Monte Carlo dose engine for radiotherapy treatment planning.

> **Status: pre-1.0 research software.** The physics, both backends and the influence-matrix
> pipeline are complete and test-pinned, but the software is young, and the validation it has
> passed is stated precisely on the
> [validation status](https://pyradmc.readthedocs.io/en/latest/validation/) page rather than
> claimed broadly. **Do not use it for anything clinical, now or later, without independent
> validation.**

The primary product is a **beamlet-resolved dose influence matrix (Dij)** for photon IMRT/VMAT
planning: sparse CSC columns with a per-entry statistical uncertainty, computed on CPU and CUDA
from a single physics source by tagging every history's whole secondary family with its beamlet
of origin. Scheduling — grouping, chunking, batch merging, which GPU gets which column — cannot
change the matrix by one bit (test-pinned). Measured end to end on a laptop RTX 4070 at
planning statistics: **~1.1e7 histories/s**, i.e. a 100-beamlet 6 MeV field at 2–3 %
per-beamlet sigma in single-digit seconds. This archived timing used the former
200 keV electron cutoff; it is not a throughput claim for the current 25 keV default.

![One physics source compiled three ways, and the throughput gap](https://raw.githubusercontent.com/e0404/pyRadMC/main/docs/assets/warp_backend_demo.png)

The same 6 MeV beam computed with the reference interpreter and with the Warp compilation of
the *identical* physics source on CPU and CUDA (`examples/warp_backend_demo.py`). The
depth-dose curves agree within their error bands; the bars show why the backend exists.

![One Dij column, the fluence-sum identity, and a wedge plan recombined from the matrix](https://raw.githubusercontent.com/e0404/pyRadMC/main/docs/assets/dij_demo.png)

The point of the whole exercise (`examples/dij_demo.py`): one beamlet's dose column with the
truncated tail visible (left); the open field recombined from the columns at unit weights
against an independently simulated open field (middle — columns partition the field exactly);
and a wedge plan as `Dij @ weights`, no re-simulation (right), which is the loop a
treatment-plan optimizer runs thousands of times.

## Install

```bash
pip install pyRadMC              # reference backend; NumPy and SciPy only
pip install "pyRadMC[warp]"      # production backend, CPU and CUDA
pip install "pyRadMC[ct]"        # CT image reading (SimpleITK)
```

Until the first tagged release reaches PyPI, install from a clone instead:
`pip install -e ".[warp]"`.

| Backend | Role | Devices |
|---|---|---|
| `ref` | correctness oracle; never optimized | CPU (NumPy) |
| `warp` | production | CPU, CUDA |

Warp needs no CUDA toolkit to install and runs on the CPU without a GPU; CUDA is used when a
device is present. The two backends are validated against each other statistically — CPU and
GPU results are never bit-identical, but each is bit-reproducible on its own device for a
given seed.

Both backends reuse deterministic Goudsmit-Saunderson tables from
`~/.cache/pyradmc/gs-grid`. The reference sampler loads existing nodes and grows
the stored window on demand, so fresh processes reuse previous table builds.
The 512 angular cells now use logarithmic CDF spacing to retain rare large-angle
scattering at unchanged table size, with stratified construction draws reducing
finite-table noise. Run `python -m examples.gs_tail_demo` for
the angular comparison; see [table construction](docs/data.md#multiple-scattering-table-cache).

## Small photon fields

The default electron production/transport cutoff is now **25 keV**, replacing
200 keV. At 200 keV, the water CSDA path still to be transported is about 0.45 mm,
large enough to distort a 0.5 mm field. The lower cutoff restores lateral dose
transport; it also produces more secondary electrons. Recompile tabulated electron
data at the new cutoff before using old material files.

Run `python -m examples.minibeam_cutoff_demo --device cuda:0` for the spectral
heterogeneous-density example. Measured spectral brass/water comparisons, the
unchanged photon cutoff, and remaining interface limitations are documented in
[small-field accuracy](docs/minibeam.md). Brass material support remains experimental.
The inverse-range lookup retains the zero-range cutoff endpoint, preventing
artificially stalled collisional loss in fine-step convergence checks.
Tabulated nuclear scattering now interpolates the reduced first transport cross
section across sparse EEDL angular energies and integrates the angular PDF product
exactly. Rebuild material tables to apply the
correction; see [data compilation and example](docs/data.md#sparse-eedl-angular-energies).
GS sampling resolves rare large-angle tails with logarithmic probability cells
at unchanged table size and scattering strength. Run `python -m examples.gs_tail_demo`;
[measured limitations](docs/minibeam.md#sparse-eedl-angular-interpolation) include
an unresolved brass entrance-dose regression.

Circular-hole slabs on a hexagonal lattice are available through
`pyradmc.geometry.holes.HexagonalHoleCollimator`. The builder paints explicit
solid/air voxels, preserving collimator scatter and secondary transport. See
[hole-array geometry and example](docs/minibeam.md#circular-holes-in-a-hexagonal-array)
for 2 mm holes at 4 mm pitch on a 0.1 mm XY grid and its rasterization limits.

## Quick start

```python
from pyradmc import AnalyticCrossSections, HostRNG, PencilBeamSource, ReferenceEngine, VoxelGrid

grid = VoxelGrid.uniform_water(shape=(16, 16, 16), spacing=(1.0, 1.0, 1.0))
xs = AnalyticCrossSections(geometry_densities=grid.max_density_by_material())
source = PencilBeamSource(energy=6.0, position=(8.0, 8.0, -1.0), direction=(0.0, 0.0, 1.0))

result = ReferenceEngine(grid=grid, cross_sections=xs, rng=HostRNG()).run(
    source, n_histories=80_000, n_batches=10, seed=20260726
)
result.dose          # MeV/g per emitted history, on the scoring grid
result.dose_sigma    # batched 1-sigma
result.provenance    # version, seed, cutoffs, backend, device, cross-sections
```

Swap in `WarpEngine(grid=..., cross_sections=..., device="cuda:0")` for the production backend —
the `run` signatures are identical. Everything importable from the top-level `pyradmc`
namespace is public API.

From here, the [documentation](https://pyradmc.readthedocs.io/) carries the rest:
[getting started](https://pyradmc.readthedocs.io/en/latest/getting-started/) (GPU runs, the
influence matrix, pencil-beam kernels, a tour of the `examples/`),
[validation status](https://pyradmc.readthedocs.io/en/latest/validation/) — read it before
trusting a number — and
[cross-section data](https://pyradmc.readthedocs.io/en/latest/data/) (the engine ships no
libraries; the tabulated backend compiles from the IAEA EPICS evaluations, digest-verified).

## Contributing

Read [`AGENTS.md`](AGENTS.md) before contributing — it is the governing document, written for
human and agentic contributors alike; [`CONTRIBUTING.md`](CONTRIBUTING.md) is the short version
of the mechanics. Work lands on `develop` through squash-merged pull requests; `main` carries
releases only.

## License

Apache-2.0. See [`LICENSE`](LICENSE).

Native CT scoring can use `pyradmc.scoring.grid.OrientedScoringGrid`: a rigidly
placed scoring grid bins deposits directly in native coordinates while transport
remains axis aligned. Run `python -m examples.oriented_scoring_demo` for a small
water example and figure. The local RT06071 full-head/weighted-Dij study is
experimental; its input restrictions and batch workflow are described in
[the minibeam notes](docs/minibeam.md).
