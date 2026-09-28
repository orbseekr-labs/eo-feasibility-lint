# Real-world validation (blind benchmark) — 2026-09-28

This document records a blind comparison between labels written from the
specification and what `eo-feasibility-lint` 0.1.0 (catalog `2026-08-15.1`)
actually reports, for requirements taken from public, real-world documents.

> **This is not an accuracy estimate.** The sample is small (25 runnable cases),
> skewed toward agency mission-requirement documents, and was labelled by
> applying the tool's own specification. Agreement shows that the implementation
> behaves as its specification says on real-world inputs. It does not show that
> the verdicts are right for real EO projects, and it does not measure usefulness.

Data: [`benchmark/real-world-cases.yaml`](../benchmark/real-world-cases.yaml),
inputs in [`benchmark/cases/`](../benchmark/cases/), raw tool outputs in
[`benchmark/actual/`](../benchmark/actual/). The regression test
[`tests/test_benchmark.py`](../tests/test_benchmark.py) re-runs every case
offline and requires byte-identical JSON.

## Method: three blind roles

| Order | Role | Did | Did not |
| --- | --- | --- | --- |
| 1 | **Extractor** | Collected 30 cases from 7 GitHub READMEs (pinned commit SHAs) and 6 agency documents (ESA Sentinel-1/-2/-3, LSTM and CHIME Mission Requirements Documents; a NASA SBG overview). Recorded each requirement with its framing: `required`, `desired` or `used-as-input`. | Run the tool, or read its catalog, tests or outputs. Only the public README was read, to learn the input dimensions. |
| 2 | **Labeler** | Mapped each case to a tool input file and wrote expected portfolio verdicts, per-mission verdicts and finding codes. Worked from `README.md`, `SPECIFICATION.md`, the input schema, and first-party mission pages that the labeler checked independently. | Run the tool, or read `src/`, the catalog data, the tests, the examples or the reports. |
| 3 | **Runner** | Ran the unmodified tool on every input (`eo-feasibility-lint check <case> --format json`, no `--mission` overrides). Saved the outputs and hashed them. Only then opened the labels and compared. | Read the labels, or anything except the case inputs and extracted requirements, before the outputs were recorded. Edit any label or input. |

Hash-freeze evidence:

- The labels and inputs were frozen with SHA-256 at **2026-09-28T04:18:54Z**.
  - `expected.yaml`: `a5e13481a07717220ee2b31655e0ab0992ebf7ba37aa9b56b408a0df41eac52f`
  - `requirements.yaml`: `ccb19b8bbf88744f06069b2352bc630234dd83b1a4ae2afab64b6f64aa87fbb4`
  - one hash for each of the 25 case inputs
- Before the run, all frozen hashes were re-verified (`shasum -a 256 -c`, all OK).
- The tool outputs were produced and hashed at **2026-09-28T04:20:04Z**. That was before the labels were opened.
- The case inputs in `benchmark/cases/` are byte-identical copies of the frozen inputs.

### Mapping policy (set by the labeler)

- Only `required` items are mapped. `desired` items are mapped only when a case has no required item.
- Where a document gives both a threshold and a goal, the threshold is mapped.
- A range "a–b" maps to its upper bound b.
- A strict bound "< X" maps to the inclusive maximum X.
- Product or service update frequency is not treated as revisit.
- `output.kind` was chosen by the labeler. It was not extracted from the source.
- `candidate_missions` was omitted except in RW-005, so all five catalog missions were evaluated.
- Capabilities the schema cannot express were left out, and those cases are marked `partial` fidelity.

## Results

| Case | Source | Mapped requirement (tool input) | Expected | Actual | Expected findings | Actual findings | Match | Mismatch reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RW-001 | GitHub AS-youKnow/urban-heat-stress | not testable (used-as-input only) | n/a | not run | n/a | n/a | n/a | n/a |
| RW-002 | GitHub nlebovits/gee-urban-clim | not testable (used-as-input only) | n/a | not run | n/a | n/a | n/a | n/a |
| RW-003 | GitHub FaranIdo/stpred | not testable (used-as-input only) | n/a | not run | n/a | n/a | n/a | n/a |
| RW-004 | GitHub Ojas-Rohatgi/Deforestation-Detection | modality_any_of=sar_c_band; output=model_inference | CONDITIONAL | CONDITIONAL | EFL201, EFL802 | EFL201, EFL802 | yes | — |
| RW-005 | GitHub Yingjie4Science/SNAPP | optical_max_gsd_m=30; output=derived_product | CONDITIONAL | CONDITIONAL | EFL801 | EFL801 | yes | — |
| RW-006 | GitHub bangboomben/ha-nasa-firms | not testable (used-as-input only) | n/a | not run | n/a | n/a | n/a | n/a |
| RW-007 | GitHub SylviaChebetEMTH/Crop-Analysis | not testable (used-as-input only) | n/a | not run | n/a | n/a | n/a | n/a |
| RW-008 | ESA S2 MRD | spectral_bands_all_of=visible+nir+red_edge+swir; optical_max_gsd_m=20; max_nominal_revisit_days=10; min_single_pass_swath_km=200; output=instrument_measurement | PASS | PASS | EFL201, EFL202, EFL301, EFL401, EFL402, EFL701 | EFL201, EFL202, EFL301, EFL401, EFL402, EFL701 | yes | — |
| RW-009 | ESA S2 MRD | optical_max_gsd_m=30; output=derived_product | CONDITIONAL | CONDITIONAL | EFL201, EFL801 | EFL201, EFL801 | yes | — |
| RW-010 | ESA S2 MRD | optical_max_gsd_m=10; output=derived_product | CONDITIONAL | CONDITIONAL | EFL201, EFL301, EFL801 | EFL201, EFL301, EFL801 | yes | — |
| RW-011 | ESA S2 MRD | optical_max_gsd_m=10; output=derived_product | CONDITIONAL | CONDITIONAL | EFL201, EFL301, EFL801 | EFL201, EFL301, EFL801 | yes | — |
| RW-012 | ESA S2 MRD | optical_max_gsd_m=300; output=derived_product | CONDITIONAL | CONDITIONAL | EFL201, EFL801 | EFL201, EFL801 | yes | — |
| RW-013 | ESA S2 MRD | optical_max_gsd_m=10; output=derived_product | CONDITIONAL | CONDITIONAL | EFL201, EFL301, EFL801 | EFL201, EFL301, EFL801 | yes | — |
| RW-014 | ESA S2 MRD | optical_max_gsd_m=1000; output=derived_product | CONDITIONAL | CONDITIONAL | EFL201, EFL801 | EFL201, EFL801 | yes | — |
| RW-015 | ESA S2 MRD | optical_max_gsd_m=30; output=derived_product | CONDITIONAL | CONDITIONAL | EFL201, EFL801 | EFL201, EFL801 | yes | — |
| RW-016 | ESA S1 MRD | modality_any_of=sar_c_band; max_nominal_revisit_days=14; min_single_pass_swath_km=240; output=instrument_measurement | PASS | PASS | EFL201, EFL401, EFL402, EFL701 | EFL201, EFL401, EFL402, EFL701 | yes | — |
| RW-017 | ESA S1 MRD | modality_any_of=sar_c_band; max_nominal_revisit_days=2; output=derived_product | FAIL | FAIL | EFL201, EFL401, EFL801 | EFL201, EFL401, EFL801 | yes | — |
| RW-018 | ESA S1 MRD | modality_any_of=sar_c_band; max_nominal_revisit_days=1; output=derived_product | FAIL | FAIL | EFL201, EFL401, EFL801 | EFL201, EFL401, EFL801 | yes | — |
| RW-019 | ESA S3 MRD | modality_any_of=thermal_ir; thermal_max_gsd_m=500; max_nominal_revisit_days=1; output=derived_product | FAIL | FAIL | EFL201, EFL401, EFL801 | EFL201, EFL401, EFL801 | yes | — |
| RW-020 | ESA S3 MRD | optical_max_gsd_m=500; max_nominal_revisit_days=3; output=derived_product | FAIL | FAIL | EFL201, EFL401, EFL801 | EFL201, EFL401, EFL801 | yes | — |
| RW-021 | ESA S3 MRD | spectral_bands_all_of=thermal_ir; output=derived_product | CONDITIONAL | CONDITIONAL | EFL202, EFL801 | EFL202, EFL801 | yes | — |
| RW-022 | ESA LSTM MRD | modality_any_of=thermal_ir; spectral_bands_all_of=visible+nir+swir+thermal_ir; optical_max_gsd_m=50; thermal_max_gsd_m=50; max_nominal_revisit_days=3; must_support_night=True; output=derived_product | FAIL | FAIL | EFL201, EFL202, EFL302, EFL401, EFL501, EFL501 or EFL502 (labelled alternative), EFL502, EFL801 | EFL201, EFL202, EFL302, EFL401, EFL501, EFL502, EFL801 | yes (codes: labelled alternative) | — |
| RW-023 | ESA LSTM MRD | modality_any_of=thermal_ir; thermal_max_gsd_m=50; output=derived_product | FAIL | FAIL | EFL201, EFL302, EFL801 | EFL201, EFL302, EFL801 | yes | — |
| RW-024 | ESA LSTM MRD | thermal_max_gsd_m=150; must_support_night=True; output=derived_product | CONDITIONAL | CONDITIONAL | EFL201, EFL501, EFL502, EFL801 | EFL201, EFL501, EFL502, EFL801 | yes | — |
| RW-025 | ESA LSTM MRD | must_support_night=True; output=derived_product | CONDITIONAL | CONDITIONAL | EFL501, EFL502, EFL801 | EFL501, EFL502, EFL801 | yes | — |
| RW-026 | ESA LSTM MRD | modality_any_of=thermal_ir; must_support_night=True; output=derived_product | CONDITIONAL | CONDITIONAL | EFL201, EFL502, EFL801 | EFL201, EFL502, EFL801 | yes | — |
| RW-027 | ESA CHIME MRD | spectral_bands_all_of=visible+nir+swir; optical_max_gsd_m=30; max_nominal_revisit_days=12.5; output=instrument_measurement | PASS | PASS | EFL201, EFL202, EFL401, EFL402 | EFL201, EFL202, EFL401, EFL402 | yes | — |
| RW-028 | ESA CHIME MRD | spectral_bands_all_of=visible+nir+swir; optical_max_gsd_m=30; output=derived_product | CONDITIONAL | CONDITIONAL | EFL201, EFL202, EFL801 | EFL201, EFL202, EFL801 | yes | — |
| RW-029 | NASA SBG overview | spectral_bands_all_of=visible+nir+swir; optical_max_gsd_m=45; output=instrument_measurement | PASS | PASS | EFL201, EFL202 | EFL201, EFL202 | yes | — |
| RW-030 | NASA SBG overview | modality_any_of=thermal_ir; spectral_bands_all_of=thermal_ir; thermal_max_gsd_m=60; max_nominal_revisit_days=4; output=instrument_measurement | FAIL | FAIL | EFL201, EFL202, EFL302, EFL401 | EFL201, EFL202, EFL302, EFL401 | yes | — |

"Match" means the portfolio verdict and every per-mission verdict are equal to the label. Per-mission finding-code multisets were also compared; they are listed per case in `benchmark/real-world-cases.yaml`.

For RW-022, the labeler did not decide between two codes for the night support of Landsat's reflected-optical bands, and wrote `EFL501|EFL502` × 3. The tool emits `EFL501` × 3 because the catalog gives `false` for those bands. This is within the labeled alternative, and the verdict is FAIL either way.

## Metrics

| Metric | Value |
| --- | --- |
| Cases extracted | 30 |
| Testable (tool input written) | 25 |
| Not testable (all requirements framed `used-as-input`) | 5 (RW-001, 002, 003, 006, 007) |
| Invalid input (exit 2) | 0 |
| Expected UNKNOWN / actual UNKNOWN (portfolio) | 0 / 0 |
| Exact portfolio verdict matches | **25 / 25** |
| Per-mission verdict matches | **123 / 123** |
| **False FAIL** (actual FAIL where the label is not FAIL): portfolio / per-mission | **0 / 0** |
| **False PASS** (actual PASS where the label is CONDITIONAL, UNKNOWN or FAIL): portfolio / per-mission | **0 / 0** |
| CONDITIONAL disagreements | 0 |
| Finding-code set: exact / subset / superset | 24 / 0 / 0, plus 1 inside the labeled alternative (RW-022) |
| Per-mission finding-code multisets | 24 exact, 1 inside the labeled alternative (RW-022) |
| Cases with partial-fidelity mapping (requirements the schema cannot express) | 5 (RW-008, 021, 027, 028, 029) |
| Mapping-ambiguity notes recorded by the labeler | 66, spread over all 25 cases |
| Label confidence high / medium / low | 14 / 9 / 2 (low: RW-010, RW-019) |
| Actual portfolio verdicts PASS / CONDITIONAL / FAIL | 4 / 14 / 7 |
| CONDITIONAL cases where only `output.kind` (EFL801/EFL802) keeps the best mission from PASS | 12 of 14 |

Mismatch classification: **no mismatches**, so there is nothing in any class (TOOL_BUG 0, CATALOG_STALE 0, INPUT_MAPPING_AMBIGUITY 0, OUT_OF_SCOPE 0, EXPECTATION_ERROR 0).

## Limitations

- **Evidence-limited and skewed sample.**
  - 23 of the 30 cases come from agency mission-requirement documents (mostly ESA). Those documents specify future missions, not end-user projects.
  - All 7 GitHub cases state mainly the data the authors *used*. Only 2 of them were testable.
- **No all-weather cases.** No examined source states an explicit all-weather requirement, so `weather.must_support_all_weather` is untested here. SAR appears in only 4 of the 25 testable cases.
- **The labeler chose `output.kind`.**
  - Maps and indices were labelled `derived_product` (EFL801, CONDITIONAL). Mission instrument requirements were labelled `instrument_measurement`.
  - This single choice decides PASS versus CONDITIONAL in 12 of the 14 CONDITIONAL cases.
- **Update frequency versus revisit.**
  - Product or service cadences ("daily", "within 12 h") were deliberately not mapped to revisit.
  - Where revisit *was* mapped, the tool compares the value with the equator-nominal constellation revisit, not with revisit at the user's latitude. This affects RW-017 and RW-018 (Arctic and European coastal use cases).
- **Not expressible in the v0.1 schema.** The following were omitted from the inputs:
  - hyperspectral contiguous 400–2500 nm (RW-027 to RW-029, reduced to the visible/nir/swir families)
  - MWIR 3.7 µm (RW-021)
  - per-band resolution tables (RW-008, collapsed to 20 m)
  - polarisation, latency, dynamic range, NEDT and overpass time

  A PASS or CONDITIONAL on those cases reflects the tool's scope, not real-world feasibility.
- **Shared reference.** The labeler worked from the same specification and from the same first-party pages as the catalog. Agreement is therefore expected when the implementation follows its spec, and systematic errors shared by the spec and the labels would not be detected.
- **Open catalog question found during the comparison.** A USGS EROS article, "Nighttime Imaging Grows Landsat's Science Value", says Landsat OLI SWIR bands can detect intense heat sources such as fires at night. That imaging is by special request only. The catalog models Landsat reflected-optical night support as `false`. Whether SWIR hot-target detection should count as `occasional` night support is a semantic question, and no change was made. It affects only the per-mission codes in RW-022 (EFL501 or EFL502), not any verdict.
