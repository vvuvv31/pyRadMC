# Decision record

Why the engine is the way it is. Most of these are **negative results** — things built,
measured, and then not shipped — which are the expensive kind to rediscover.

This is a record, not a specification. Where it disagrees with `AGENTS.md` or the code,
they are right and this is stale. Live constraints that still bind are in `AGENTS.md`
section 8, not here.

## Sampling and variance reduction

**Correlated sampling across beamlets is the default.** Keying each beamlet's histories
on the within-beamlet index rather than the global history index makes corresponding
histories replay the same interaction sequence, differing only in entry position. It
roughly **halves** the renormalized plan-dose error at matched per-beamlet sigma, and is
never worse on raw plan quality. Established by optimizing on one noisy Dij and scoring
on a second, independent ground truth across six statistics levels, in water and through
a heterogeneity (`examples/noise_bias_study.py`). `correlated=False` survives only as a
test instrument.

**Compton splitting ships off** (`PHOTON_SPLIT_N = 1`). Built, unbiased, test-pinned at
N = 2 — and dormant. Efficiency `1/(σ²·time)` came out below 1 on the analytic-water Dij,
then again on a phase-space source at **0.75 / 0.48 / 0.28 for N = 2 / 4 / 8** — worse,
monotonically. Splitting at the first Compton lets copies decorrelate only *after* that
scatter, so variance reduction saturates far below 1/N while cost grows linearly. It also
cannot reach the low-dose tail, which is fed by rare wide-angle scatters that uniform
splitting cannot target. Turning it on needs a new measurement, not an argument.

**Russian roulette on sub-0.5 MeV photons is always on.** The threshold sits just below
the 511 keV annihilation line so annihilation photons stay analog. Unbiased by
construction and test-pinned against a roulette-free run.

**Weight linearity holds only above the roulette weight cap.** Below it, a boost chain
that crosses the cap in one run but not another diverges that history's stream — and
correlated sampling then replays the divergence into every column. Fair per run, pinned
statistically below the cap, bit-pinned above it.

## Electron transport

**Goudsmit-Saunderson is the shipped multiple-scattering model**, with a substep energy
fraction of 0.20. The Gaussian small-angle model remains as the `"gaussian"` instrument —
a model whose approximations differ from the default's is what makes the default's error
visible.

**GS was adopted for accuracy, not speed.** The speed premise was measured and
**falsified**: at the previously shipped substep fraction the angular cap was inert
throughout soft tissue, so larger steps were never available there.

**The multiple-scattering strength is the Class-II first transport moment of the
Moliere-screened Rutherford law**, replacing the
Rossi-Greisen/Highland core width `(14.1/pv)^2 / X_0` on 2026-09-04. Goudsmit-Saunderson
pins `<cos theta> = exp(-s N sigma_tr)` exactly, so the retained strength is
`2(N_A/A)[Z^2 sigma_tr + Z(sigma_tr - sigma_tr,M^hard(E, ECUT))]`: nuclear elastic plus
subthreshold electron scattering. The above-ECUT Moller moment is removed because the
transport loop applies those deflections explicitly. This preserves the soft e-e
component that no other part of the loop supplies while eliminating the Class-II double
count exactly. Highland lacks the energy-growing `ln(1/eta) - 1` factor: the restricted
moment is 1.25x Highland at 1 MeV, 1.68x at 10 MeV and 1.77x at 15 MeV in water. The
hard correction is 0.4-4.2 % of the unrestricted `Z(Z+1)` strength over 0.5-15 MeV,
versus about 13 % removed at all energies by a nuclear-only `Z^2` approximation in water.
Measured on monoenergetic pencil kernels in water against EGSnrc and TOPAS (1 mm voxels,
1 mm axial shell): the integrated build-up at half dmax went from 0.95-0.97 of EGSnrc to
0.99-1.01 and the central-ray excess from +4 / +14 / +19 % (1 / 6 / 15 MeV) to +3 / +2 /
+7 %, inside the TOPAS-vs-EGSnrc spread; beyond dmax nothing moved (CPE). Broad-beam
electron R50 now matches EGS4 (Rogers & Bielajew, Med. Phys. 13, 687 (1986), Table III)
to +0.4-0.9 % at 5-20 MeV and +2.3 % at 3 MeV, where Highland read 8-9 % long — note that
E0 = 2.33 R50 is the AAPM/ETRAN approximation, not the EGS relation, and would mis-set a
gate by 3-8 % at 5-10 MeV. The tabulated
implementation combines EEDL nuclear scattering with the same analytic subthreshold
electron moment (its 15 MeV axial excess fell from +11 % to +8 %; at 6 MeV it now
overscatters slightly, build-up 1.03, because EEDL's nuclear moment is interpolated
across its 0.256-10 MeV shape gap and sits 1.1-1.3x the closed form at 1-6 MeV).
These ratios describe the historical normalized-moment interpolation, superseded
on 2026-11-02 by reduced-transport interpolation (see [data compilation](data.md#sparse-eedl-angular-energies)).
Stated omission: no Mott (spin-relativistic) factor on the
closed-form moment, a few percent at `beta -> 1` in low-Z media.

**Each electron substep is capped at the next voxel face.** Without it a step carried one
medium's stopping power across a boundary into the neighbour's mass, producing a
single-voxel interface spike — **1.95x before, under 1.4x after** at a pure density step.
Residual interface structure is second-order (the hinge can still deflect the short
post-hinge segment across the face) plus genuine interface dosimetry.

**Positrons stay Møller-approximated** — no Bhabha, annihilation at rest. If upgraded,
both land together as the new default, with a test showing the dosimetric effect.

## Cross-section data

**Berger-Seltzer ICRU-37 stopping is the default even where EEDL data exists.** The EEDL
route is provenance-consistent but sits ~4 % from ESTAR; the analytic form is
ESTAR-exact. Provenance purity lost to accuracy.

**Coherent scattering uses EPDL form factors**, replacing a Thomson-limit angular model.

**Enabling a coherent channel requires refitting pair production.** The analytic pair
channel is calibrated against water totals that *already include* coherent scattering, so
adding a real coherent channel without recalibrating against coherent-free totals
double-counts attenuation. Channels must come from one consistent decomposition of one
library.

**2 %/2 mm on the depth-dose gate is not reachable, and the benchmark is the limiter.**
The tabulated backend barely differs from the analytic one here — the analytic photon
*total* was already NIST-calibrated, so a more accurate channel split moves the shape
little. Decisively: *widening* the phantom toward the infinite-field limit makes the
deep-tail residual **worse**, which is the lateral-integrated pencil beam overestimating
the benchmark's finite-field, 6 mm-tube scoring at depth. The gate stays 5 %/3 mm until a
fully specified benchmark exists. See `AGENTS.md` section 8.

**Cross-section libraries are pinned by SHA-256 and verified fail-closed.** These bytes
*are* the cross-sections; a corrupted cache or a silent upstream revision would surface as
unexplained drift in a dose gate rather than as an error.

## Reference GS startup

**The reference sampler shares the existing persisted GS grid, growing its requested
rectangle on demand.** On 2026-09-05, the existing 21 MB, 5,148-node Warp cache covered
all 494 nodes requested by the collimated Dij ledger test and all 914 requested by the
boundary-truncation test. Loading it solves their repeated construction cost without a
new format or construction-version bump. Cold reference runs grow a dense rectangle;
this can build unrequested interior nodes, but preserves compatibility with the eager
reader. Owned, immutable rows enter the existing node memo so source caches do not
retain obsolete grid allocations. Both grid writers share the existing thread lock.

**Eager reference initialization loses badly on short cold runs.** Interleaved lazy /
eager / lazy / eager measurements on Windows, Python 3.13.14, NumPy 2.4.6, using the
6 MeV analytic-water window and unchanged production build constants:

| Cold workload | Lazy persistence | Eager initialization | Nodes, lazy / eager |
|---|---:|---:|---:|
| One GS sample at 1 MeV, theta-squared 0.003 | 0.587 / 0.613 s | 30.27 / 32.49 s | 4 / 3,562 |
| Collimated Dij, 900 histories | 93.95 / 96.73 s | 32.30 / 31.17 s | 777 / 3,562 |

These initial measurements predate the shared rectangle filler described below.
The lazy rectangle adds some first-run cost relative to the original memory-only
constructor, but avoids a mandatory roughly 31-second startup for even one sample.
This favors lazy persistence (option b); a separate node-store format is unnecessary.

**Sharing column parallelism does not by itself accelerate incremental cold fills.**
The review follow-up factors both builders through `_fill_rectangle`, preserving the
existing threshold of 256 **new** nodes per fill and the 16-worker cap. The reference
sampler requests a whole 2x2 bracket under one lock and saves once. It also returns
immediately when a defensive disk re-read finds coverage. Both writers recover from
save failures and clean up temporary files. Inverse-CDF resolution now participates
in disk and memory identities; existing version-1 grids remain readable only at their
historical 4096-bin resolution. Construction and format are unchanged, so version 1
remains appropriate.

Interleaved before/after/before/after cold measurements against the initial persisted
implementation, with the same production constants and 900-history Dij:

| Cold workload | Before review fixes | After review fixes |
|---|---:|---:|
| One GS sample | 0.615 / 0.599 s | 0.592 / 0.595 s |
| Collimated Dij, 900 histories | 91.81 / 93.30 s | 95.91 / 93.75 s |
| Dij nodes built | 777 | 777 |
| Dij saves / bytes written | 14 / 18,163,256 | 11 / 18,032,692 |

The largest revised extension adds 180 nodes, so **none starts a pool**. These results
do not demonstrate a cold transport speedup and do not recover eager initialization's
roughly 31-second result. A single sample drops from three saves to one; most later
growth events already extend only one axis. Larger extensions now share eager
parallelism, with serial/parallel reconstruction pinned byte-equal after clearing
the node memo. Changing worker-selection policy would need a separate measurement.

Warm review comparisons also ran before/after/before/after in fresh processes against
the same stored grid. Direct 900-history Dij invocations took 1.014/0.982 s before and
1.006/0.997 s after; direct calls to `test_interface_voxel_is_not_spiked` took
61.69/61.12 s before and 60.83/60.92 s after. All made zero node builds and zero saves.
These direct timings exclude pytest initialization and are distinct from the original
pytest timings below.

The review's full fast-suite comparison ran A/B/A: 193.70 s (A), 200.13 s (B),
191.81 s (A), all passing. A runs the 1,292 common tests, excluding the cache-specific
test files; B runs all 1,312 tests, including the twenty cache cases (ten added by
this review). These wall times include pytest startup. Windows reported 2,200 MHz;
they remain laptop measurements with warm transport-grid coverage. Production-dose,
column-sigma and CSC bytes also matched each target's prior result on reference,
Warp CPU and CUDA independently.
The Warp CPU check also extended a four-node reference cache by 3,558 nodes through
the shared parallel filler, then CUDA read that completed grid without rebuilding;
both reproduced their own baseline dose, sigma and CSC bytes.

**Fresh processes reuse the cached nodes without changing dose.** A restores the
original `gs_scaled_deflection_table(exp(i / bins), exp(j / bins), n_u=nodes)` reference
lookup; B uses the persistent lookup. Each measurement starts a fresh interpreter,
with the same existing grid available to Warp in both cases. Times below measure
`pytest.main`, including its initialization. Histories, seeds and tolerances are
unchanged. The named tests ran A/B/A/B; successful full-suite runs ran B/A/B. An earlier
full baseline affected by a competing solve and a pytest-cache shutdown permission
error was excluded. Windows reported nominal clock states of 1,466–2,200 MHz; these
interleaved measurements are not controlled-power hardware baselines.

| Fast workload | Before | After |
|---|---:|---:|
| Full suite | 330.17 s, 1,292 passed | 214.33 s, 1,292 passed; 219.70 s, 1,302 passed |
| `test_weighted_column_ledger_closes` | 76.67 / 91.90 s | 1.606 / 1.451 s |
| `test_interface_voxel_is_not_spiked` | 195.24 / 171.28 s | 67.23 / 63.50 s |

The last full run includes all ten added cache tests. Named-test median paired speedups
are 55.5x and 2.80x, with zero node rebuilds in either cached test. These are standalone
test timings: the boundary test's earlier roughly 84-second *in-suite* profile could
reuse nodes from preceding tests; a standalone cold process builds all 914.

The production 900-history Dij's dose, column sigma and CSC structure were byte-equal
between uncached reference construction, a warm grid, and both cold grid strategies.
Warp CPU and CUDA each reproduced their own prior dose, sigma and CSC bytes when
reading a reference-generated grid; the CPU check extended its partial rectangle
before upload. No comparison requires equality across targets. The fast suite,
strict mypy, ruff, pre-commit and strict documentation build passed. Cutoffs, step
fractions, truncation and node construction are unchanged.

## Scoring and interfaces

**The dose grid is decoupled from the transport grid.** Any origin, spacing or shape,
including subregions, with **no coverage requirement in either direction**: a deposit
inside the CT but outside the dose grid goes to an *unscored* ledger bucket, never a
clamped edge voxel — clamping would corrupt edge dose. Per-voxel mass is rebinned by exact
separable voxel overlap, which is also what *defines* dose-to-medium for a mixed voxel.
Scoring a 2 mm CT on a 3 mm grid is ~0.30x the memory, the largest plan-calculation lever.

**`dose_to_water` is a scoring-output selection, not a physics toggle.** Transport, RNG
streams and the energy books are identical in both modes; only the per-deposit tally
weighting differs. It is refused in KERMA mode, where there is no tracked electron to
evaluate the stopping-power ratio on.

**Sources take engine-frame geometry only.** Gantry and couch rotation stay out of the
core — adapters map frames, for beam sources exactly as for the CT adapter.

**Collimation wrappers consume zero random numbers.** Deterministic Beer-Lambert
transmission weights preserve correlated Dij replay; a sampling implementation would not.

## Rejected

**Track-repeating / macro-MC: rejected on two independent grounds.** Its accuracy failure
modes — air, interfaces, bone, lung, penumbra — are precisely where Monte Carlo on CT
earns its keep, and both known fixes destroy the speed premise. Independently, the Dij is
not transport-bound enough for it to pay.

**Dij denoising: out of scope, permanently.** The optimizer exploits statistical noise; it
exploits denoising bias too, and that bias is spatially correlated and therefore worse.

**Quasi-Monte Carlo source sampling: measured neutral.** Built and unbiased, variance
reduction factor ≈ 1.0 over 48 seeds. Per-voxel Dij dose is transport-dominated counting,
which source-side QMC cannot help.

**A non-radial primary fluence envelope: measured negative.** A fixed-collimator term
C(x, y) on top of the radial fluence is the one extra degree of freedom the virtual-source
literature suggests when diagonals disagree, and the Halcyon beam data does show its
diagonal reading 0.2 to 1.0 per cent above the crossline at equal radius over r = 7-11 cm.
It is not a fluence structure. The differential is flat in measurement-plane coordinates
and grows with depth at fixed fan angle, where anything fixed in the collimator would
scale with divergence and dilute with depth; and the simulation, whose fluence is radial
by construction, already reproduces it (4.0 against 4.3 per cent at the strongest bin). It
is phantom scatter asymmetry near the crossline's field edge, transported for free in both
channels. The model-minus-measurement azimuthal residual is not coherent above its ~1 per
cent noise floor, so there is nothing to fit. Keep the diagnostic: plane-coordinate
flatness plus depth growth reads "scatter"; fan-coordinate constancy would read "fluence".

**Single-GPU micro-optimization is exhausted.** Persistent threads, register and occupancy
tuning, texture-memory reads and step-fraction changes all measured neutral or negative.
The kernel is divergence- and latency-bound. What remains is multi-GPU or algorithmic.

## Hazards learned the hard way

**Kernel compilation could leak into host modules.** Loading the Warp physics patched
`sys.modules`, and any module first imported inside that window bound the kernel-side
`uniform` permanently — silently breaking the *reference* backend for the rest of the
process. Fixed by evicting modules first imported in the window; regression-pinned in a
subprocess test, because an in-process test cannot reproduce the import ordering.

**Verify GPU clocks before believing any timing on the development laptop.** Its power
state has been observed drifting several-fold, and once ran at 210 MHz under full load —
faking a uniform multi-fold regression across every CUDA benchmark. The tell is CPU rows
getting *faster* while GPU rows get uniformly slower. Only interleaved-median ratios are
trustworthy there.

**Micro-optimizing kernel arithmetic measures zero.** Shared logarithm nodes and float
quantization changed nothing: nvcc already eliminates the redundancy. The bottleneck was
never arithmetic.

**A phase space must be normalized per original primary**, not per stored record. Caught
by a demo whose absolute dose was wrong, not by a unit test; now regression-pinned.

**Flipping a validated default re-rolls every fixed-seed statistical test.** Expect around
a 1 % trip rate across the suite, and repair those by fixing the oracle, never by
loosening the tolerance.

## 2026-10-30: Resolve submillimetre fields with a 25 keV electron cutoff

The former 200 keV default locally terminates a water CSDA path of about
0.45 mm. A 6 MV spectral, 0.5 mm brass-slit comparison with TOPAS identified
suppressed lateral dose transport: decreasing the GS step fraction by four
changed the 2–4 cm FWHM from 0.6303 to 0.6405 mm, whereas rebuilding all
restricted electron tables at 50/25 keV gave 0.6906/0.6948 mm (TOPAS
0.6955 mm). The 50→25 keV surface-dose change remained resolved; 25→10 keV
was below the measured ~0.5–0.8% SEM. Adopt 25 keV as the single default,
with PCUT and the step fraction unchanged. This is a resolution decision,
not a fitted normalization. Old cutoff-specific tables require rebuilding.

The runnable spectral density-heterogeneity example and validation test measure
the dosimetric effect. Detailed conditions, uncertainty definitions and remaining
brass/interface limitations are in [minibeam.md](minibeam.md). The post-hinge
voxel-boundary approximation remains; a deterministic geometric counterexample
alone does not establish its contribution to the observed dose residual.

A separate fixed-seed CUDA fast-math regression reproduced E'/E > 1 by one
float32 ULP in Compton sampling. Enforce the exact upper kinematic bound in
the pure scalar sampler. This prevents negative recoil instead of clipping
scored dose, and does not fit the reference to backend output.

A further fixed-seed replay separated a second round-off source from Compton:
a rounded bremsstrahlung cap followed by two electron-energy subtractions could
leave terminal kinetic energy near −1e−8 MeV. Return the capped photon and
nonnegative final kinetic energy from one shared scalar energy budget. This
enforces E = k + scheduled_loss + E_final to float precision, with E_final >= 0;
it does not change the thin-target emission law or clip the scored dose.
## Inverse restricted-range zero endpoint (2026-10-30)

A water-entry replay at ECUT=PCUT=10 keV and electron step fraction 0.0125
exposed a numerical stall: the inverse range table's flat lower extrapolation
could return its first-node energy above ECUT after a positive mass path. A
deterministic constant-stopping regression demonstrates the missing loss. The
inverse lookup now connects that node to E(0)=ECUT linearly in residual mass
path, the local constant-stopping approximation to the continuous-loss relation
(Sempau et al. 2000, doi:10.1088/0031-9155/45/8/315). Generic cross-section
extrapolation, table nodes, production cutoff/step defaults and Dij truncation
are unchanged. The reference backend is not adjusted. Host and compiled
CPU/CUDA analytic regressions and a terminal-electron CUDA transport probe
validate the endpoint. This numerical correction is separate from deciding an
electron boundary algorithm or fitting minibeam dose to TOPAS.

The endpoint correction does not remove forward/inverse interpolation mismatch
at arbitrarily small mass steps. A subsequent air-distance-cap probe reproduced
zero loss away from the inverse-table floor. Treat distance refinement as
numerically contaminated until independently checked; a private midpoint
stopping-power instrument is being measured, without adding a production flag
or changing the reference. A log-energy probe is not a dose-error bound.

## 2026-11-02: Interpolate the nuclear transport quantity

Sparse EEDL angular distributions and denser total elastic rates have different
energy curvature. Interpolating their normalized angular mean independently
transfers the total-rate curvature into the first transport cross section.
Form sigma1 at angular-energy nodes and interpolate its reduced value
`(p*beta)^2 * sigma1`, removing the leading Coulomb dependence analytically.
A synthetic Coulomb-scaling test fails with the old method by 24% at 1 MeV.
Independent installed DPWA differential data support the new energy trend;
these research data are not a new library dependency. No fitted scattering
normalization or runtime model switch is introduced. The forward angular tail
remains omitted and the screened-Rutherford angular family remains unchanged.

This data correction reduces a fixed-packet CT core-dose bias from -2.70% to
-0.47% against the original GATE option3 benchmark. A full five-beam calculation,
also refining the rectilinear XY geometry, changes the regional dose bias from
-4.01% to -1.61% against independent 32M-event GATE references per beam. These
are case-specific regional integrals, not per-voxel or universal accuracy.

An independent quadrature correction integrates `(1-mu)*p(mu)` exactly for
the EEDL piecewise-linear PDF. The quadratic product is not trapezoidal:
`p=2+mu` on `[-1,1]` gives a normalized moment5/6, not1/2. Analytic,
cell-subdivision and independent Gauss-quadrature tests establish this without
an external dose fit. On the full common CT packet, exact product integration
changes the core energy by -0.081% (paired-block SEM0.034 percentage points)
relative to reduced interpolation alone. Full-head exact-product controls give
regional biases of -1.001% and -1.104% for side039 and central051. Both
corrections require rebuilding compiled material data; they do
not change transport kernels or electron production cutoffs.


## 2026-11-02: Resolve rare GS tails at fixed table size (candidate)

Equal-probability compression replaces the widest-angle tail by one
conditional mean. It preserves the first transport moment but suppresses
higher moments, especially for short, face-capped electron steps. Use CDF
edges `u_i=expm1(10*i/n)/expm1(10)` and integrate the empirical inverse CDF
within each interval. Probability-weighted normalization keeps the same
first-moment anchor before cosine clipping. No scattering strength or dose
scale is fitted; the raw screened-Rutherford GS construction is unchanged.
The sampler still draws once and the default row still has512 entries.
Construction-cache version3 includes the CDF spacing and the stratified raw
construction described below, and rejects older rows.
Goudsmit & Saunderson (1940), doi:10.1103/PhysRev.57.24.

An analytic screened-Rutherford tail regression demonstrates the second-moment
compression error independently of transport. Two independent upstream
physical-packet populations give core-dose changes of+.412 and+.305 percentage
points in fine-face CT replay, with paired-block SEM.082 and.059 points.
The native-face change is unresolved. The central full-head GPU control improves the fixed regional bias from
-1.104% to -0.740% against32M GATE events, with64M GPU histories and a
paired change of+.368% (SEM.026 percentage points). The separate brass
entrance0--4mm remains discrepant: -3.352% with tail512 versus -3.485%
with corrected EEDL alone. This candidate is not yet promoted to the
working minibeam branch. The logarithmic map is representation
resolution, not a user-selectable physical model. Raw-construction sampling
error and rare cosine clipping remain limitations.


The long-step construction oracle retains its historical maximum probability
cell size1/4096. Equal entry counts are unequal resolution after the CDF map
changes:4096 logarithmic cells have maximum probability.002439, versus
.0002441 for4096 uniform cells. For this construction-only instrument choose
`ceil(4096*span/(1-exp(-span)))` entries, from the CDF derivative bound.
At the unchanged200000 draws, fixed seed,20 histogram bins andp>.001 gate,
the independently composed Lambda500 comparison changes fromchi2=45.17,
p=.000648 tochi2=18.08,p=.517. This corrects the oracle's resolution, not
its threshold or source count. Production512-cell compression keeps separate
first-moment, higher-moment and exact discrete-sampler tests.

## 2026-11-02: Reduce GS construction noise (candidate)

The fixed finite raw GS population is part of the numerical approximation.
Increasing it from 2^19 to 2^21 or 2^22 changes a fixed-packet CT core integral
nonmonotonically, by +0.366% and +0.146%. Do not select a construction seed or
count by its agreement with GATE. Instead, for each set of k active single
collisions, randomly assign one jittered inverse-CDF draw from each stratum.
Every lane's marginal remains uniform; Poisson multiplicities, azimuth law,
scattering strength and default raw count are unchanged. McKay et al. (1979),
doi:10.1080/00401706.1979.10489755.

Against analytic GS transport-moment ratios at four screening/path points,
16 fixed construction seeds and 65536 raw samples, stratification reduces mean
squared shape error by factors of 12--43. A deterministic single-collision test
checks exact CDF stratum coverage independently of dose. The persistent grid
construction version advances to 3 so previous IID rows cannot be reused.

A broader independent raw-moment ensemble uses 64 seeds, 65536 samples,
eta=0.001/0.01/0.1 and Lambda=0.05/0.5/2/50, without first-moment
renormalization. Its first, second, fourth and eighth transport-moment mean
biases are within 1.56 ensemble SEM of the analytic values. This does not
prove zero bias. Low-order MSE usually decreases, but the eighth moment at
Lambda50 and eta0.001/0.01 has about 1.90/1.97 times the IID MSE. The
12--43-fold improvement above applies to its specific shape-ratio diagnostic,
not every moment or key.

An independent central full-head 64M-history GPU control has a -0.812% regional
bias against 32M GATE events, versus -0.740% with IID tail512. This is not an
additional dose-fit improvement. The held-out brass entrance changes by
-0.108% (paired SEM 0.116 percentage points), retaining an unresolved -3.456%
bias. Selection is based on independently measured construction stability;
the selected five-beam check is now complete. At 64M GPU histories per
column versus 32M GATE events per column, the five-column fixed ROI bias is
-1.027%, compared with historical -4.010% and the earlier reduced-EEDL/fine2
result -1.611%. The combined changes include raster refinement and cannot
be attributed to angular physics alone. GPU plan-integral SEM is 0.034%,
computed from eight complete summed plan blocks. Existing GATE column
uncertainties do not establish a plan SEM. Fixed 1 mm geometry-window PVDR
biases at native y=-100/-50/0/50 mm are -1.898/-1.829/-0.414/-2.253%.
Some worsen relative to the intermediate fine2 result; integral-dose improvement
is not universal improvement of the peak/valley structure. The completed 0.1 mm fine-profile
check uses 128M GPU histories/model and four independent 32M GATE repeats.
At native y=-97.5/-47.5/2.5/52.5 mm, profile-area biases are
-0.043/-0.959/-1.228/-0.132%, with ratio SEMs
0.392/0.211/0.610/0.445 percentage points. Native y is not skin depth.
Each area is integrated before its repeat/block SEM is estimated.

The fixed-seed constant-SPR Dij identity test exposed a numerical-oracle
limitation after the angular construction changed which voxels were sparsely
hit. At the default 1e-9 MeV score quantum, one voxel differed by 3.75e-13
MeV/g per primary: 0.6 normalized quanta, but 2.72e-5 relative. Repeating
the same 800 histories, seed and transport at 1e-10 and 1e-11 MeV score
precision reduces the maximum relative discrepancy below 1e-6. The identity
test now explicitly uses the finer tally as a numerical test instrument,
retaining the original 1e-5 assertion, histories and seed. Its bounded energy
is far below int64 capacity; the fixture restores and recompiles default
constants afterwards. Production tally precision is unchanged. Default-score
forward identities and CPU/CUDA scheduling tests remain separate checks.

The real multi-material compiler validation also retained the historical
200 keV cutoff while compiling at the current 25 keV default. Explicit
library-enabled runs reproduce the source's expected cutoff-mismatch error.
The oracle now imports ECUT_MEV, matching the previously corrected water
compiler validation; no stopping-power or mixing tolerance is changed.


An independent full-plan GATE ensemble checks reference statistics without
replacing or selecting the original reference. Eight complete plan blocks,
each five independent4M-event columns, total160M events. Only the passive
scorer is cropped to the exact ROI; all physical inputs, source strata,
transport configuration and original-script hashes are checked unchanged.
The new ensemble mean differs from the original reference by+0.0435%.
Its regional relativeSEM is0.0465%, versus GPU0.0335%; GPU bias against
this independent ensemble is-1.070% with independent ratioSEM0.0567
percentage points. Thus the roughly1% regional discrepancy is resolved beyond
current source sampling noise, although this integral does not locate its cause.

Fixed1mm-window PVDR bias against this independent ensemble is
-2.268/-2.819/-0.008/-1.864%, with ratioSEMs0.867/1.086/1.380/0.979
percentage points at native y=-97.5/-50/0/50mm. The first window differs from
the primary plot's-100mm because the passive ROI ends at-100mm. These plan
SEMs come from complete summed plan blocks, retaining peak/valley and spatial
covariance; the original reference's planSEM is still not inferred from its
column or voxel sigmas. These are exploratory case-specific comparisons,
not a newly commissioned voxelwise or multi-case accuracy guarantee.


The selected-model held-out step scan completes all18 arms:2/5/10cm brass,
1/3/5slits, native and fourfold face caps,128M GPU histories per arm against
original16M TOPAS references. All288 energy ledgers pass. The entrance
response is geometry-dependent and the thick-brass deficit remains; no
uniform step-default change is adopted. See docs/minibeam.md for regional
means and paired source-block uncertainties. The boundary approximation
requires a consistent path/material/scattering replacement, not dose scaling.
