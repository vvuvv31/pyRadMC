# Submillimetre photon fields: cutoff and TOPAS comparison

The electron production/transport default is **25 keV kinetic** (formerly
200 keV). PCUT remains 50 keV and the GS step fraction remains 0.2. Rebuild
restricted stopping, Møller and Class-II scattering tables with the new cutoff;
do not relabel an old table. The engine checks table/cutoff consistency.

## Why the cutoff matters

Subthreshold recoil energy and the residual energy of stopped electrons are
scored locally. In water the CSDA path at 200 keV is approximately 0.450 mm,
comparable with a 0.5 mm slit. At 50 and 25 keV it is approximately 0.043 and
0.012 mm. Local scoring at 200 keV suppresses lateral transport and makes the
peak artificially narrow. Increasing photon histories reduces noise but does
not remove this bias.

A controlled 6 MV spectral brass/water study kept the geometry, source,
normalization and seeds fixed and rebuilt the restricted tables for each cutoff.
At 2–4 cm water depth, central slit-minus-solid-slab FWHM was:

| Cutoff / instrument | GPU FWHM (mm), ±1 bootstrap SD |
|---|---:|
| 200 keV, original step fraction 0.2 | 0.6303 ± 0.0079 |
| 200 keV, step fraction 0.05 | 0.6405 ± 0.0096 |
| 50 keV | 0.6906 ± 0.0111 |
| 25 keV | 0.6948 ± 0.0093 |
| TOPAS (80M incident photons) | 0.6955 ± 0.0074 |

These cutoff instruments used 16 independent 1M-history batches. Reducing
50 → 25 keV changed the surface central dose by −2.57 ± 0.89%; 50 keV was
therefore insufficient. A further 25 → 10 keV test changed central dose by
+0.46 ± 0.77%, +0.54 ± 0.46%, and +0.03 ± 0.51% at surface, 2–4 cm,
and 8–10 cm. This supports 25 keV at the measured precision; it does not
prove convergence for every field or material.

An executable, external-data-free measurement of the dosimetric effect is:

```bash
python -m examples.minibeam_cutoff_demo --device cuda:0
```

It compares paired independent batches for a 6 MV spectral 0.5 mm field with
a low-density slab (water composition, 0.25 g/cm³), and saves
`examples/minibeam_cutoff_demo.png`. This is a density-heterogeneity instrument,
not a validated lung composition or a substitute for the brass comparison.
`tests/validation/test_small_field_cutoff_effect.py` pins the central-dose
fraction effect without changing statistical tolerances.

## Comparison conditions and scope

The brass study uses a point source 100 cm upstream of the water entrance,
the Ali–Rogers Varian 6 MV spectrum, a 4 × 4 cm aiming field at the entrance,
Cu70/Zn30 mass fractions, density 8.5 g/cm³, straight 0.5 mm slits,
2 mm pitch, and a 1 cm exit-to-water gap. The baseline is a single slit in
2 cm brass; the scan compares 2/5/10 cm brass and 1/3/5 slits.
The baseline uses 80M photons per backend and per open/closed case; scan
cases use 16M. TOPAS source histories are shared across configurations and
are not counted as independent additional source samples.

Dose is absolute MeV/g per emitted photon, with no fitted scale, smoothing,
or output clipping. Scoring uses 0.1 mm lateral and 2 mm depth bins and
averages across the full 16 cm y extent. These are integrated profiles, not
local two-dimensional slit-center doses. SEM is computed after ROI integration
inside each independent batch. Closed-slab subtraction is paired within a
backend. PVDR is the per-batch ratio of a fixed 0.3 mm central peak window to
the mean of the two nearest 0.3 mm valley windows, projected with depth;
it is not a noisy maximum/minimum ratio. Single slits have no periodic PVDR.

The experimental material profile uses EPDL/EEDL elemental data with
Geant4-compatible mean excitation/density-correction inputs. Independent ESTAR
validation of this alloy has not been performed. It is a local validation
profile, not a shipped commissioned brass data library or a production
collimator/Dij API.


## High-statistics result with the new default

After the cutoff and Compton endpoint fixes, the 80M-photon baseline gives:

| Water depth (cm) | GPU FWHM (mm) | TOPAS FWHM (mm) | Central absolute dose difference (%) |
|---|---:|---:|---:|
| 0–0.4 | 0.5766 ± 0.0051 | 0.5836 ± 0.0068 | +1.76 ± 0.70 |
| 2–4 | 0.6882 ± 0.0048 | 0.6955 ± 0.0074 | −1.10 ± 0.39 |
| 8–10 | 0.7485 ± 0.0053 | 0.7497 ± 0.0082 | −0.47 ± 0.43 |

FWHM is measured from the paired slit-minus-closed mean profile, with bootstrap
SD across independent paired batches. Central dose uses |x| < 0.25 mm; its
uncertainty is the combined independent-backend ratio SEM. These are different
estimators. The previous 200 keV 80M peak widths were 0.5472, 0.6230 and
0.7113 mm. Width agreement does not imply statistical equivalence of dose:
the remaining −1.10 ± 0.39% central offset at 2–4 cm is resolved at this
precision. Closed-slab and slit total water-energy differences are −0.010 ±
0.031% and −0.021 ± 0.031%, but this background-dominated agreement must not
obscure the paired slit-excess energy difference (about −1.20 ± 0.49%).

An 8M-per-backend broad-cone control gives total water-energy differences of
+0.041 ± 0.070% (monoenergetic 6 MeV) and +0.350 ± 0.091% (6 MV spectrum),
with 2–18 cm integrated depth-profile relative RMS differences of 0.31% and
0.64%. These controls use analytic water data, whereas the brass study uses
experimental tabulated materials. The existing 5%/3 mm, ≥90% PDD assertions
were also exercised through CUDA at 1/2/6 MeV with both analytic and compiled
water data. This is a CUDA adaptation of the existing benchmark assertions,
not a claim that the full slow reference validation suite was rerun.

At 2–4 cm depth, all nine 16M scan configurations have central dose differences
between −0.62% and +0.46%, with combined SEM of 1.0–1.6%. The scan central
window is 0.3 mm (distinct from the baseline's 0.5 mm window). PVDR results are:

| Brass thickness (cm) | Slits | GPU PVDR ±SEM | TOPAS PVDR ±SEM |
|---|---:|---:|---:|
| 2 | 3 | 1.233 ± 0.010 | 1.226 ± 0.009 |
| 2 | 5 | 1.228 ± 0.009 | 1.223 ± 0.009 |
| 5 | 3 | 1.638 ± 0.016 | 1.630 ± 0.014 |
| 5 | 5 | 1.605 ± 0.014 | 1.599 ± 0.013 |
| 10 | 3 | 2.484 ± 0.029 | 2.443 ± 0.038 |
| 10 | 5 | 2.361 ± 0.025 | 2.343 ± 0.032 |

All 14 final raw baseline/scan GPU case arrays were audited batch by batch:
the nine negative voxels present before the numerical endpoint corrections
became zero, with maximum relative L1 map change below 9e−13. The raw dose
arrays were not clipped. The complete fast suite passed (1313 passed, one
optional-CT skip); the full slow reference validation suite was not run.

Compact numerical measurements and independent-batch central scores are
archived in `tests/validation/data/minibeam_cutoff_20261030.json` and `.csv`;
see that directory's README for provenance and reproduction limits.

## Floating-point endpoint regression

A fixed-seed CUDA fast-math probe found a scattered/incident Compton energy
ratio of 1.00000012, beyond its exact upper bound of 1. This can create
negative recoil energy and tiny negative dose quanta. The scalar sampler now
caps the returned ratio at 1, consistent with the analytic kinematic support
(Kahn sampling; PENELOPE-2018, doi:10.1787/32da5043-en). The regression test
samples 128M ratios and enforces nonnegative recoil, without a numerical
tolerance. The reference is not calibrated to the GPU.

A second, independent CUDA replay found tiny negative terminal electron energies
after a capped bremsstrahlung event: rounding the cap k = E − reserved_loss,
then subtracting k and the reserved second-half loss, left residuals around
−1e−8 MeV. The shared scalar `capped_bremsstrahlung_budget` now returns both
the capped photon energy and the residual projected onto its nonnegative
kinematic support. Host and device transport use this same budget. A float32
regression demonstrates the uncorrected overdraw and verifies the energy budget
to float precision; a CUDA probe and the original offending batch provide
independent checks. Dose arrays are never clipped to conceal negative tallies.



## Five-slit cross section below 1% statistical uncertainty

A separate precision study used **1.28 billion incident photons**, split into
128 independent 10M-history batches (seed `3510031 + 137*batch`). The 64M pilot
used distinct seeds and is excluded from this total. Source and materials are as
above; brass thickness is 10 cm, with five straight 0.5 mm slits at 2 mm pitch
and a 1 cm air gap. Production physics, cutoffs and step fraction are unchanged.

The x–y image averages dose over **water depth 2–4 cm**, with 0.1 mm x bins
and 5 mm y bins. It is a slab average, not a thin transverse plane. For all
968 scored-bin centers in |x|≤6 mm, |y|≤20 mm (all five peaks and valleys,
no dose-threshold exclusion), the estimated relative 1-sigma dose SEM is:

| Metric | Relative SEM |
|---|---:|
| Worst bin | 0.845% |
| Median bin | 0.494% |
| 95th percentile | 0.713% |
| Worst point of the y-averaged lateral profile | 0.285% |

SEM is estimated across independent batches after integrating each batch's ROI.
This meets the requested <1% pointwise statistical uncertainty in the declared
ROI; it is not a simultaneous confidence bound or a transport-accuracy claim.
No precision claim is made for the low-dose region outside that ROI.

The central PVDR is 2.4953 ± 0.0034 for y=±20 mm, using 0.3 mm peak/nearest
valley windows and ratios of mean ROI doses with covariance retained. Averaging
across the full 16 cm y extent instead gives 2.3370 ± 0.0032, consistent with
the earlier scan's definition. The two values must not be mixed when assessing
agreement. Outer fixed-ROI peak doses average 0.6374 ± 0.0009 of the central
peak; geometric vignetting of straight slits remains relevant.

Compact dose/SEM measurements are archived in
`tests/validation/data/five_slit_precision_20261030.json` and `.csv`. The local
study `local_fiveslit_precision_20261030/` retains per-batch arrays, energy
ledgers, scripts and figures (`five_slit_xy_dose.png`, `five_slit_profile.png`).
Dose figures use microGy per 1e9 incident photons; CSV/NPZ use MeV/g per emitted
photon. No smoothing, output clipping or fitted normalization was applied.

## Boundary-related sensitivity study at 25 keV

A subsequent controlled study fixed the electron cutoff and material tables and
compared GS step fractions 0.2/0.05/0.0125. With 64M paired incident photons per
open-slit case, shrinking the step fraction sixteenfold changed central absolute
dose by −0.390 ± 0.464%, +0.032 ± 0.247%, and −0.104 ± 0.271% at 0–0.4,
2–4, and 8–10 cm depth (±SEM, |x| < 0.25 mm, full y).

To locate the sensitivity, local diagnostic copies applied the fine step only to
steps starting in brass/air, only to steps starting in water, or everywhere.
Other materials retained fraction 0.2; these are test instruments, not shipped
physics options. Each open/closed case used 32M photons and paired seeds.

| Depth (cm) | Brass/air-only central dose change (%) | Brass/air-only net FWHM change (mm) | Water-only net FWHM change (mm) |
|---|---:|---:|---:|
| 0–0.4 | +0.002 ± 0.865 | +0.00090 ± 0.00494 | −0.00443 ± 0.00813 |
| 2–4 | +0.092 ± 0.025 | +0.00066 ± 0.00041 | +0.01877 ± 0.00789 |
| 8–10 | +0.036 ± 0.026 | +0.00012 ± 0.00037 | +0.00820 ± 0.00866 |

Dose errors are paired SEM; FWHM errors are paired bootstrap SD. The 2–4 cm
width response to shrinking steps everywhere (+0.01887 mm) is reproduced
primarily by the water-only instrument. It must not be assigned to the brass/air
boundary approximation. The surface upstream-only result remains too uncertain
to exclude an effect of order 1%.

A passive local scorer recorded forward/reverse photon, electron and positron
crossings at the brass exit and water entrance. Analytic rays tested directions,
weights, interpolated charged energy and histogram conservation. All 16-batch
three-step open/closed dose arrays were bit-identical with/without scoring on the
same CUDA device; the extended default 64 batches and finest first 32 were also
checked. With 64M photons, central exit electron kinetic-energy current changes
+22.45 ± 2.60% under sixteenfold global shrinking, while central water-entrance
current changes −0.97 ± 2.87%. These are crossing currents through a 0.5 mm
band, not dose changes. Repeated crossings are retained and only marginal
histograms are stored; this is not a particle replay or a separate electron-dose
calculation. No new TOPAS exit-spectrum comparison was performed.

The 10 cm three/five-slit PVDR study (16M/configuration) did not establish
monotonic convergence: changing fraction 0.05→0.0125 changed central PVDR by
+2.92 ± 1.44% / +3.64 ± 1.27%. Picking the intermediate fraction because it
happens to agree better with TOPAS would be unjustified. Production defaults
remain unchanged.

These experiments measure step sensitivity, **not an upper bound on the boundary
algorithm's error**. Region selection uses starting material, and an energy-step
reduction may leave geometry-limited air steps unchanged. An interface-specific
absolute-distance or validated boundary-transport comparison remains necessary.
Measurements, source hashes, uncertainty definitions and per-batch energy/seed
checks are archived in `tests/validation/data/boundary_step_20261030.json`.
The local study and passive scoring copies are separate from production code.

## Remaining limits

### Small steps and the inverse-range endpoint

The inverse restricted-range table has a strictly positive first node. Flat
extrapolation below that node used to return an energy above ECUT, allowing a
sufficiently small substep to produce zero collisional loss. This was reproduced
in a 10 keV, step-fraction 0.0125 water-entry replay. The generic cross-section
lookup still clamps outside its grid; the inverse restricted-range lookup now
connects its first node to the physical endpoint E(0)=ECUT, linearly in residual
mass path. This approximates constant restricted stopping only across that last
interval. It leaves the table nodes and all accuracy-defining defaults unchanged.

Constant-stopping analytic regressions cover positive sub-node loss, the zero
endpoint and the existing interpolation above the first node. Compiled CPU/CUDA
tests check the same endpoint and monotonicity. A separate 1,000-electron CUDA
transport probe at 10 keV and fraction 0.0125 finishes with energy balance. The
reference backend already integrates to zero residual range and is unchanged.
Overnight fine-step and nonwater-distance instruments use explicitly recorded
private copies with this correction; an uncorrected stalled variant is excluded,
not interpreted as a converged physical result.

A paired five-slit, 10 cm brass check used 128 independent 10M-history batches
per variant at unchanged 25/50 keV cutoffs and fraction 0.2. Across the six
declared depth slabs, the largest measured fixed peak/valley ROI dose change
was −0.00214 ± 0.00103% (surface central peak, ±paired SEM). The final production
implementation and the independently compiled private endpoint instrument
produced identical saved batch dose maps on this CUDA device. This small
default-parameter effect is separate from the remaining GPU/TOPAS discrepancy
and is not a universal boundary-error bound.

### Extremely small mass steps remain a separate numerical limit

Restoring the zero-range endpoint does not make independently interpolated
forward and inverse range tables exact inverses. Under an absolute air-step
cap, their round-trip offset can exceed the intended energy loss. A float64
log-energy probe at a 6.25 micrometre air step found zero collision loss at
about 47% of sampled energies; this sampling is neither a transport spectrum
nor a dose-error estimate. Float32 cancellation is an additional concern.
Consequently, the original nonwater distance-cap series cannot by itself
measure convergence of brass/air boundary transport. QA-only midpoint
integration of the existing restricted stopping table is checked independently
and compared at fixed histories; it is not a new production physics option.
The reproducible diagnostic and its dose controls are recorded in the overnight
measurement archive. No step size is selected for agreement with TOPAS.

### External water-material conventions

Matching composition, density and mean excitation energy is insufficient to
match every material quantity. The original TOPAS `MatchWater` uses 75 eV,
as does the source registry, but its generic-mixture density-effect parameters
differ from the registry's published liquid-water row. A passive metadata probe
of the actual TOPAS process verified the difference. An independent GPU-only
QA table rebuilt water restricted stopping and CSDA range with that convention,
leaving all photon, radiative, Moller and scattering tables, other materials,
cutoffs and the original TOPAS reference unchanged. In 128 paired 10M-history
batches, central peak dose changed by +0.18% to +0.38% across the six slabs;
residuals narrowed to approximately −0.17% to −0.62% but remained jointly
resolved. This isolates a benchmark material-definition contribution, not a
reason to replace the production liquid-water parameters or fit the reference.
The matching profile is explicitly an external-validation instrument.

Across the nine approved 2/5/10 cm by 1/3/5 slit configurations, a separate
256M-photon-per-backend/variant check used the same unfitted material definition.
At 2–4 cm, central peak residual point estimates narrowed from −0.17% to −1.00%
to −0.04% to −0.54%. Both variants use the endpoint repair, keeping that tiny
numerical effect separate from the material effect. Point estimates and their
uncertainties, including less favorable depth/region results, remain in the
archive; improved agreement is not equivalence.

### Per-column precision remains distinct from plan precision

The 64 independent, untruncated three-dimensional matrices also measure
per-column uncertainty without combining correlated column sigmas. Each matrix
transports 128M histories over 20 columns. Averaging all 64 gives 409.6M histories
per column; these matrices retain the initial transport implementation.
Within each column's data-derived high-dose mask (at least 50% of its global
mean maximum over scored water), the 95th percentile of voxel SEM is about
0.66–0.74% for the central six columns and 2.60–2.62% for blocked outer columns.
Outer-column worst-cell SEM still reaches 3.33%. These are diagnostics, not a
full-column or organ-specific acceptance gate.

The blocked columns' small scatter contribution inside the central 2–4 cm ROI
is much noisier: its own ROI-relative high-dose p95 SEM reaches 12.55% even in
the all-64 average. That is a different mask from each column's global high-dose
region. The actual equal-fluence plan is formed inside each independent matrix
before its variance is estimated; its global high-dose p95 SEM is 0.534% and
worst-cell SEM 0.662%. None of these guarantees low-dose-tail precision or
optimizer robustness, and full-field profile precision does not transfer to
individual Dij columns.

### Uncollimated spectral water remains a separate surface check

A 128M-photon-per-backend control removed brass entirely, retaining the 6 MV
spectrum, 4 × 4 cm aiming field, 100 cm point source, 12 cm upstream air and
water scoring grid. Original-table central-dose differences were −0.234% to
+0.163% at 1–16 cm, but +2.380 ± 0.212% in the 0–4 mm surface slab (batch SEM).
The matched-water QA table gave +2.582 ± 0.213% at the surface and did not
provide a universal correction. Thus surface residuals must not all be assigned
to brass geometry or to water-material conventions. Fixed-count air-removal
and water-only step controls are recorded separately in the overnight archive.
Removing upstream air leaves a +2.280 ± 0.217% surface residual; refining the
water energy-step fraction from 0.2 to 0.003125 changes the surface dose by
−0.082 ± 0.070%. Native 2 mm depth bins localize the largest residuals to the
first few millimetres. These controls do not establish strict step convergence.

An independent 32M-photon TOPAS control refines lateral bins from 0.1 to
0.025 mm and rebins them to the same physical cells before comparison. Its
surface shift relative to the original 128M reference is +0.163 ± 0.341%; the
GPU-minus-fine-reference residual remains +2.114 ± 0.348%. Original references
are retained; binning changes may also change TOPAS navigation steps.

A separate GPU-only PCUT 50/25/10 keV diagnostic uses one extended photon table
with a 5 keV lower limit, unchanged electron tables and same-table 50 keV
controls. Lowering PCUT from 50 to 10 keV changes surface central dose by
−0.017 ± 0.015% with upstream air, −0.013 ± 0.013% without air, and
−0.004 ± 0.071% in the brass five-slit case. All uncertainties here are batch
SEM. The small observed cutoff sensitivity does not explain the broad-water
surface residual or justify a default change. An initial unsupported-table
attempt was excluded before dose analysis and retained with its exclusion
record. The numerical endpoint repair, water-definition QA tables, scoring
resolution and photon-cutoff experiments remain distinct.

The existing continuous-loss scorer subdivision instrument was also isolated
at fixed 128M histories per variant and unchanged trajectories, seeds, tables
and transport settings. Replacing each half-segment midpoint by path pieces
no longer than 3.125 micrometres changes surface central dose by
−0.0147 ± 0.0005% with air and −0.0143 ± 0.0006% without air. Three nested
piece sizes and all six slabs are retained. This small scoring sensitivity
does not explain the roughly 2.3% broad-water surface residual; it does not
validate the underlying angular transport or post-hinge boundary treatment.
The production scoring default is unchanged.

### Material-boundary approximation

The condensed-history electron step caps distance to the next voxel face using
the incoming direction. A sampled hinge can redirect the second segment across
a face while loss/scattering still use the starting material. This is a known
boundary approximation, especially relevant at brass/air interfaces. Clipping
the segment after sampling would also invalidate the sampled loss and angle;
no such unvalidated boundary change is included here.

Straight parallel slits vignette a divergent source: in 10 cm brass the outer
slits at ±4 mm have only about 0.079 mm uncollided projected width at the water
surface. A fall in outer/central dose is therefore partly geometric. It should
not be removed by adjusting electron transport.

The lower cutoff increases transport work; historical 200 keV throughput
figures do not describe the new default. No controlled cutoff-speed comparison
or universal small-field accuracy claim is made. The separate endpoint repair
was timed in 12 interleaved standalone pairs on an RTX 2080 Ti: repaired/initial
median runtime ratio 1.00078, descriptive paired-bootstrap interval
[0.99878, 1.00129]. Clocks were observed but not locked; no clear local runtime
change was resolved, and this does not measure the cutoff tradeoff. Remaining statistically resolved
absolute-dose discrepancies must be reported even when peak widths agree.

### RT07575 heterogeneous CT measurement

A local AP five-slit benchmark on the 35-slice RT07575 head CT used 512M
upstream photons per backend, split into 64 independent batches. The geometry
retains the 10 cm Cu70/Zn30 collimator, 0.5 mm straight slits and 2 mm pitch.
Both engines share the illustrative pyRadMC HU calibration, quantized density,
composition, I and scoring masses. It is not a commissioned CT calibration.

At six predeclared CT-box depth slabs from 3–4 to 20–21 cm, central fixed-window
peak differences (GPU/TOPAS minus one) range from −1.17% to +0.15%, adjacent
valley differences from −0.12% to +1.60%, and PVDR differences from −2.01% to
−0.52%. Independent-batch difference SEM is 0.45–0.73% for peak/valley doses.
Mass-weighted whole-tissue regional differences range from −0.31% to +0.45%;
the 20–21 cm bone-interface region gives −1.55 ± 0.67% (1 SEM). A joint
covariance-aware peak/valley bootstrap detects residual differences (p=0.00850).

These are integrated profile/region measurements, not a voxelwise accuracy
claim: the 0.05 × 2 × 0.5 mm scoring cells have about 8.4% median voxel SEM in
the declared high-dose tissue domain. Native CT resolution remains
0.5 × 0.5 × 2 mm. TOPAS recomputes mixture density effects per density, whereas
Warp retains reference-density mass tables; numerical navigation also differs.
The finite 7 cm SI extent and single narrow field do not certify a full PTV
plan or Dij. No production physics, defaults or tables were changed for this
measurement. Full local records and figures are in
`local_rt07575_minibeam_20261031/RESULTS.md`; patient input data stay local.
