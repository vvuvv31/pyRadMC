# Validation benchmark data

## center_ray_dose_EGSNrc_intRadius6.0mm.txt

Central-axis depth dose in water from **EGSnrc (full physics)**, supplied by the
maintainer on 2026-07-10. Stored verbatim.

**Known provenance** (maintainer statement):

- Wide uniform photon beam (lateral scatter equilibrium) in a large water cylinder.
- Scored on the central cylinder of radius 6 mm; depth bins of 0.25 cm to ~50 cm.
- Monoenergetic columns from 0.05 to 7 MeV; dose in arbitrary units, no per-point
  uncertainties provided.

**Missing metadata** (recorded so nobody mistakes the gate for tighter than it is):

- EGSnrc transport parameters (ECUT/PCUT, Rayleigh on/off, brems model, EII).
- Exact cylinder radius and length; source normalization.

**How the gate uses it** (`test_ranges_and_pdd.py`): for a laterally-equilibrated
uniform beam, the central-axis dose equals the laterally *integrated* dose of a pencil
beam (pencil-kernel superposition), so the test runs a pencil beam and scores slice
sums — every history contributes at every depth. Normalization is free (least squares)
because the benchmark units are arbitrary.

Columns below ~1 MeV are not gated against the analytic backend: its cross-section layer
is an explicitly few-percent parameterization for the soft spectrum (Klein-Nishina
without binding, crude photoelectric power law, no Rayleigh). That is also why the gamma
criterion is 5%/3mm rather than 2%/2mm.

**2%/2mm is not reachable against this file, and the limiter is the missing metadata
above rather than the cross-section data** — see `AGENTS.md` section 8. Do not loosen the
5%/3mm gate, and do not expect a better data layer to close the gap; a genuine 2%/2mm
gate needs a fully specified benchmark.

## Small-field cutoff measurement (2026-10-30)

`minibeam_cutoff_20261030.json` records absolute-dose/FWHM statistics from the
80M-photon-per-case 6 MV single-slit brass/water comparison, 16M-per-case
2/5/10 cm × 1/3/5 slit scan, cutoff convergence instruments and the broad-cone
control. `minibeam_cutoff_20261030.csv` contains independent-batch central-band
open/closed scores (MeV/g per incident photon) for the legacy/default GPU and
TOPAS baseline. For each row the central band is |x| < 0.25 mm, full y average,
with the specified depth slab. Integrate before estimating SEM; the open and
closed rows in a batch are paired. GPU and TOPAS use independent source seeds.
The files are simulation measurements generated in this project, not vendor
beam data or redistributed EPICS tables.

These are archived measurements, not a test that pins random simulation outputs.
The JSON records geometry and source/table hashes; the large raw dose maps,
phase-space files and experimental alloy tables remain in the local study
folders identified there. This compact archive cannot regenerate the entire
brass study alone. The external-data-free, executable cutoff-effect measurement
is `python -m examples.minibeam_cutoff_demo --device cuda:0`; its limitations
and the brass comparison definitions are in [minibeam.md](../../../docs/minibeam.md).


## Boundary-related step sensitivity (2026-10-30)

`boundary_step_20261030.json` archives project-generated 25 keV measurements:
32M/case global and region-restricted step instruments, 16M/configuration thick
multi-slit PVDR, and 64M open-slit surface-current/absolute-dose comparisons.
Dose changes carry paired batch SEM; width changes carry paired bootstrap SD.
It includes production/scoring source hashes and checks of finite/nonnegative
raw maps, fixed seeds, actual cutoffs and energy closure. No production source
was changed for this study. See [minibeam.md](../../../docs/minibeam.md).

Passive surface spectra are marginal histograms, retain repeated crossings and
use the condensed-history segment's linear energy interpolation. They do not
provide independent particle histories, replay data or a component dose. Region
instruments choose the step fraction by starting material; they do not isolate
only actual boundary-crossing steps. These measurements establish step
sensitivity, not a certified interface-error bound. Raw local scripts, scoring
copies and large arrays are under `local_boundary_sensitivity_20261030/`; this
compact archive alone cannot regenerate the study. Local geometry metadata
retains its historical cutoff field; explicit diagnostic overrides and engine
provenance confirm that the actual cutoff is 25 keV throughout.


## Five-slit cross-section precision (2026-10-30)

`five_slit_precision_20261030.json` records the 1.28B-photon five-slit study,
source/material hashes, geometry, batch count, statistical-precision criterion
and PVDR definitions. `five_slit_precision_20261030.csv` contains dose mean and
SEM for the 968 predefined ROI bins. Coordinates are mm; dose and SEM are
MeV/g per emitted photon. The image is averaged over water depth 2–4 cm, with
0.1 mm x and 5 mm y bins. Every archived ROI bin has estimated relative 1-sigma
SEM below 1%; systematic transport/material errors are not included.

The local raw data and scripts are in `local_fiveslit_precision_20261030/`.
These files contain project-generated simulation measurements, not external beam
or cross-section data. The metadata archive cannot regenerate the experiment
alone. See [minibeam.md](../../../docs/minibeam.md) for the y-averaging distinction
from the earlier full-y PVDR scan and for the remaining physics limitations.

## Overnight GPU / TOPAS minibeam studies (2026-10-30)

`minibeam_overnight_20261030.json.gz` is a losslessly compressed JSON archive of
measurements, declared
scoring/normalization definitions, initial and final source hashes, verification
records and completion status for the overnight study. Check `complete` and
`missing_sections` before interpreting it as the complete planned ensemble.
The local raw arrays, independent-batch records, input phase spaces, scripts and
figures remain under `local_minibeam_overnight_20261030/`; `RESULTS.md` is its
Chinese entry point. The compact archive alone cannot regenerate the runs.

The full-y and local-y comparisons each use fresh independent 1.28B-photon
ensembles per backend; their ROI precision and PVDR definitions must not be
mixed. True 3D Dij measurements distinguish thresholding each independent
matrix from averaging matrices before thresholding. Repeated aggregate groups
retain whole-matrix covariance; no plan sigma is inferred from Dij column
sigmas. The study uses an experimental Cu70/Zn30 material profile and makes no
clinical accuracy claim. Earlier GPU/TOPAS runs keep the initial source; the
subsequent inverse-range endpoint repair is separately validated and does not
change the cutoff, step-fraction or Dij-threshold defaults.

Additional entries distinguish fixed central-ROI column precision from each
column's global high-dose precision. Blocked columns can be precise in their
own high-dose region yet noisy in the central scatter tail. Both masks are
data-derived diagnostics. Independent broad-water material controls and
standalone interleaved endpoint-runtime measurements retain their own counts,
seeds and clock-state limitations; neither replaces the brass comparison.

The final archive also retains broad-water air-removal, water-step and TOPAS
lateral-grid controls, same-table photon-cutoff diagnostics and existing
continuous-loss scorer-subdivision controls. The broad
surface residual persists in these controls; none supplies a fitted correction
or changes production defaults. An unsupported low-energy photon-table attempt
was excluded before dose analysis and is explicitly recorded. The portable
local `morning_results_20261030.zip` contains reports, figures and review
sources, with a SHA256 manifest; it excludes raw dose/phase-space data and the
installed simulation environment. Saved-batch recomputation of 18 key reported
measurements is an analysis audit, not another independent transport ensemble.

## Hexagonal circular-hole array (2026-10-31)

The local, uncommitted `hexagonal_holes_20261031.json` records the seven-hole
water benchmark: 2 mm
hole diameter, 4 mm nearest-neighbor pitch, 2 cm Cu70/Zn30 brass, 0.1 mm XY
transport/scoring cells and 2 mm depth bins. GPU, TOPAS identical raster
apertures and TOPAS exact circular apertures each use 32 independent batches
of 4M upstream photons. GPU/TOPAS are independent; the two TOPAS geometries
use paired source/transport seeds. Per-window integration precedes batch SEM;
pooled peaks/valleys are equal-weight means of the individual window doses.

The archive contains individual and pooled ROI estimates, input/source hashes,
normalization audit and the covariance-aware joint discrepancy test. These are
project-generated simulation measurements, not a dose acceptance threshold or
clinical data. Full arrays, sources, logs and scripts stay in the local
`local_hexholes_20261031/` directory; the compact JSON alone cannot rerun them.
See [circular-hole geometry](../../../docs/minibeam.md#circular-holes-in-a-hexagonal-array)
for the API and rasterization convention. Brass material support remains experimental.
