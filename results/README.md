# Final scientific results campaign

Accepted model: `tfm-temporal-model-v1`, main baseline
`6637b20eb4dafa35d68c766ff4370241c750def2`. This campaign uses that model;
it adds results and reporting, not equations or a new milestone.

## Experiments and comparison conventions

All new scenarios use dynamic MSIS-00, approximate `reference_noon` initialization,
quiet F107/F107a/Ap = 150/150/4, BDF rtol=2e-6, atol=1e-8,
maximum step 120 s, background 300 s and NIR 3600 s. Longitude is 0° east.
The date identifies the preceding noon/night: the extracted dawn is on the next UTC date.

| Case | Preceding date | Latitude | Available dawn SZA | Provenance |
| --- | --- | ---: | --- | --- |
| Reference | 2020-03-20 | 45°N | 99→60° | Accepted automatic M5C bootstrap plus 393.217 s continuation |
| Summer | 2020-06-21 | 45°N | 99→60° | New scenario |
| Autumn | 2020-09-22 | 45°N | 99→60° | New scenario |
| Winter | 2020-12-21 | 45°N | 99→68.426° | New scenario; 60° is unreachable |
| Equatorial | 2020-03-20 | 0° | 99→60° | New scenario |
| High latitude | 2020-03-20 | 70°N | 99→69.755° | New scenario; 60° is unreachable |

Seasonal and latitude figures compare vertical profiles at the common SZA 85/70°.
Their common dawn metrics cover 99→70°; tables also retain each full available window.
Missing SZA 60° entries are empty in CSV and explicitly unavailable in Markdown.
No concentration is extrapolated into an unattainable solar geometry.

Native saved concentration samples are retained. The SZA99 boundary and intermediate
profile values use linear interpolation of saved concentrations. At the boundary,
forcing and algebraic species are reevaluated with the accepted model, preserving
exact shell shadow and QSSA. Intermediate table values are output interpolation,
not additional ODE solutions. UTC timestamps and SZA accompany the six dawn datasets.

## Reference dawn

The automatic-initialization reference is deliberately separate from the identical-y0
frozen/dynamic sensitivity experiment. Its accepted M5C local trajectory starts at
20:00 UTC on March 20, following an approximate bootstrap from apparent noon
12:07:55.364 UTC. The accepted background grid starts at 12:00 UTC;
unchanged snapshots and source ASTs are verified before reuse. Only the extension
from 09:00 UTC to 09:06:33.217 UTC on March 21 is newly integrated to reach SZA 60°.
The reused trajectory and bootstrap retain their original tight BDF controls
(rtol 2e-8, atol 1e-10, maximum step 60 s); the short continuation uses the
production controls above. Both are recorded separately in the manifest.

Direct model output: O3 decreases substantially through dawn at the selected upper
levels. At 90 km it changes from 5.0281e8 to 5.2750e7 molecule cm^-3 between
SZA 99/60°; at 100 km, 1.8340e8→3.6527e6. At 80 km the profile is not monotonic:
9.5909e6 at 99°, 9.9255e5 at 85°, then 5.1138e6 at 60°.
O2(a1Delta) grows as illumination becomes effective. At 60 km its near-zero 99°
value increases to 6.0059e9 molecule cm^-3 by 60°; a percentage referenced to
the near-zero starting value would be meaningless. These are finite-horizon
model outputs, not an observed or equilibrated atmospheric climatology.

## Seasonal and latitude dependence

The seasonal and latitude panels compare the complete prescribed model response:
solar geometry, MSIS background and approximate noon initialization all change.
They do not isolate a photolysis-only seasonal effect or a pure geometry effect.
Use [seasonal_summary.md](tables/seasonal_summary.md) and
[latitude_summary.md](tables/latitude_summary.md) for concentrations, full-dawn
extrema and common-window changes. Concentration change percentages are omitted
when their starting value is below the recorded relevance threshold; absolute
changes remain available in CSV.

## Dynamic atmosphere sensitivity

Reused accepted M5B/M5C trajectories have **exactly identical initial concentrations**.
The comparison isolates the effect of evolving prescribed background within this
model, including its effect on chemistry and radiation. It retains the accepted
finite window ending at SZA 60.961°, without inventing its missing 60° endpoint.

| Species | Maximum | p90 | p99 | Maximum location |
| --- | ---: | ---: | ---: | --- |
| O3 | 69.212% | 20.412% | 40.531% | 83km, SZA81.551° |
| O2(a1Delta) | 24.613% | 16.690% | 20.844% | 99km, SZA95.673° |

Relative difference is `abs(a-b)/max(a,b)` where either concentration exceeds
`max(1 molecule cm^-3, 1e-6 × nominal peak)`. The atmosphere sensitivity uses
the full-run nominal peak; the accepted initialization sensitivity uses its
dawn peak. Both conventions match the original evidence. Near-zero samples are
masked in percentage figures and reported as absolute differences in the table.
Percentiles summarize saved time-height samples, not confidence bounds or uniform
SZA integration. The atmosphere comparison's largest near-zero Delta difference
is 5528.81 molecule cm^-3.

## Initialization uncertainty

The four initialization variants reuse the accepted M5A frozen-atmosphere,
artificial-equinox calculation, with the original phase clock, not a fabricated UTC
or dynamic-MSIS trajectory. Their byte hashes and compatibility with the accepted
temporal source AST are recorded. The nominal base run and tight golden share the
exact initial state and meet the accepted solver tolerance; they are not described
as bit-identical trajectories.

Scaling finite native O/H by 0.5 or 2 gives maximum relevant dawn differences of
approximately 72.50/51.08% in O3 and 71.38/70.57% in Delta. Sensitivity becomes
material above roughly 80 km, while the same scaling has much smaller effects at
lower levels. The positive missing-atom bound has a different spatial pattern,
including a 21.62% O3 sensitivity near 50 km. These are model sensitivities to
initial conditions, not solver errors. The noon initializer is an approximate
bootstrap, not validated climatology or a unique state inferred from date/location.

## Figures, data and reproduction

All eleven figures have 300 dpi PNG and vector PDF versions in [figures](figures/).
Logarithmic concentration plots omit values ≤1 molecule cm^-3 for display only;
the NPZ and tables retain the numerical values. Percentage masks use their separate
recorded relevance floors.
Captions, plotting versions and file checksums are in
[figures.json](manifests/figures.json).

| Figures | Content |
| --- | --- |
| 01–02 | Reference O3/Delta UTC–altitude heatmaps, with SZA context |
| 03–04 | Reference dawn at 60/70/80/90/100 km |
| 05 | Paired reference vertical profiles at SZA 99/85/60° |
| 06–07 | Seasonal O3/Delta profiles at common SZA 85/70° |
| 08–09 | Latitude O3/Delta profiles at common SZA 85/70° |
| 10 | Identical-initial-state frozen/dynamic relative sensitivity |
| 11 | Accepted M5A initialization sensitivity versus altitude |

The four CSV tables each have a readable Markdown counterpart:
`reference_dawn_summary`, `seasonal_summary`, `latitude_summary`,
`sensitivity_summary`. Six compact `*_dawn.npz` files retain seven dynamic species,
R_H, three algebraic species, eleven forcings, prescribed background and metadata.
`initialization_dawn.npz` retains the reused four-family concentration sensitivity.
Large full-run, native-MSIS and NIR caches stay under ignored `work/final-results`.
Raw HITRAN and licensed source bundles are never distributed.

Use the existing scientific environment with pymsis==0.12.0. Plotting additionally
needs Matplotlib; the model environment does not need to be changed to plot files.
From the repository root, with `src` and the root on PYTHONPATH:

```text
python scripts/run_final_results.py --plan
python scripts/run_final_results.py --case summer --sources LOCAL_HISTORICAL_SOURCES --hitran AUTHORIZED_HITRAN2016
# Repeat for autumn, winter, equatorial and high_latitude.
python scripts/run_final_results.py --case reference --sources LOCAL_HISTORICAL_SOURCES --hitran AUTHORIZED_HITRAN2016 --accepted-cache LOCAL_ACCEPTED_M5C_CACHE
python scripts/plot_final_results.py --mode all --accepted-initialization-cache LOCAL_ACCEPTED_M5A_CACHE
# Once canonical outputs are present, --mode all plots without private caches.
python scripts/plot_final_results.py --mode check
```

The committed canonical outputs permit inspection and verification without access
to private raw sources. Rebuilding radiation requires the authorized source files.
Reusing initialization sensitivities requires the four original accepted caches;
their fingerprints are explicit. Each scenario config and manifest records the
baseline, geometry, initialization, drivers, solver controls, source hashes,
software versions, output checksum and physical audit.

## Scope and limitations

There is no vertical transport, advection or dynamical atmosphere feedback.
Background fields are prescribed; H2O/H2 VMRs remain fixed profiles, and exterior
O3 uses the accepted reference VMR rather than date-dependent climatology.
Activity is quiet 150/150/4. Initialization is approximate and materially uncertain.
Validation is finite-horizon; no periodic attractor or observational validation is
claimed. Sensitivity experiments and interpretation must remain distinct from
direct model output. No spectroscopy or chemistry was adjusted for this campaign.
