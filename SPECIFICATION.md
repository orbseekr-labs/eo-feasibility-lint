# eo-feasibility-lint — Consolidated Technical Specification

**Version:** 0.1.0
**Status:** Frozen for v0.1.0
**Catalog baseline:** 2026-08-15
**Catalog version:** 2026-08-15.1
**Ruleset version:** 0.1.0
**Report schema version:** 0.1

---

## 0. About this document

This document is the single authoritative specification for `eo-feasibility-lint` v0.1.0. It consolidates the original frozen technical specification, all subsequent normative rulings, and every implementation decision accepted at release review. Where any earlier document disagrees with this one, **this document governs**.

### 0.1 Conformance language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT** and **MAY** are to be interpreted as normative requirements on any implementation claiming conformance with v0.1.0.

### 0.2 Stability

This specification is frozen for the 0.1.x series. Within 0.1.x an implementation MUST NOT change verdict semantics, reason-code meanings, thresholds, the requirement schema, or the JSON report contract.

---

## 1. Product definition

`eo-feasibility-lint` is a deterministic command-line linter that checks whether explicit Earth observation requirements are compatible with documented satellite mission capabilities.

It answers exactly one question:

> Does this set of stated observation requirements contain an obvious technical contradiction with documented mission capabilities?

The tool is a static analyzer, comparable to a linter or type checker, not an assistant.

### 1.1 Runtime philosophy

The runtime MUST be:

- **Deterministic** — identical input, catalog version and ruleset version MUST produce byte-identical output.
- **Offline** — no network access under any circumstance.
- **Zero-token** — no language model, no probabilistic judgement.
- **Explainable** — every conclusion names a reason code, the requirement that triggered it, the catalog value it contradicts, and the first-party source behind that value.

### 1.2 Prohibited runtime facilities

The runtime MUST NOT use LLM APIs, external APIs, web search, dynamic availability services, probabilistic inference, or undocumented heuristics.

---

## 2. Verdict semantics

Four verdicts exist:

```text
PASS  CONDITIONAL  UNKNOWN  FAIL
```

### 2.1 PASS

`PASS` means: no incompatibility was found between the explicit requirements that v0.1 knows how to evaluate and the static mission capability catalog, and no conditional or unknown constraint remains.

`PASS` **MUST NOT** be presented as a guarantee that a real EO project will succeed. In particular it does not guarantee image acquisition, clear skies, image quality, model accuracy, object-detection accuracy, economic viability, ground-truth validity, tasking availability, revisit at a particular coordinate, usable SAR coherence, or any commercial outcome.

This distinction MUST appear prominently in user-facing documentation and, per **D-9.1**, in every text report.

### 2.2 CONDITIONAL

No known hard contradiction exists, but success depends on something outside the static catalog — required processing, a model that cannot be validated from mission specifications, a non-guaranteed acquisition mode, or scheduling.

### 2.3 UNKNOWN

Feasibility cannot be determined because the supplied requirement is insufficient for the v0.1 model. The tool MUST NOT emit a meaningless `PASS` in this situation.

### 2.4 FAIL

At least one explicit requirement directly contradicts a documented mission capability.

### 2.5 Per-mission precedence

A mission verdict is the **worst** effect among its findings:

```text
FAIL > UNKNOWN > CONDITIONAL > PASS
```

A mission with no findings has verdict `PASS`.

### 2.6 Portfolio precedence

Candidate missions are **alternatives**. The portfolio verdict asks whether at least one candidate is technically viable, and is therefore the **best** mission verdict:

```text
PASS > CONDITIONAL > UNKNOWN > FAIL
```

A portfolio `PASS` means at least one candidate passed static checks. It MUST NOT be read as meaning every candidate passed.

### 2.7 Severity scale

The two precedence orders are the same total order, used in opposite directions. The numeric scale is:

```text
PASS = 0   CONDITIONAL = 1   UNKNOWN = 2   FAIL = 3
```

---

## 3. Non-goals

The following are excluded from v0.1 by design. An implementation MUST NOT provide them.

- **No natural-language requirement extraction.** A sentence such as "measure parking lot traffic every day" MUST NOT be converted into technical requirements. `objective` is human-readable metadata and MUST NEVER be parsed by the rule engine.
- **No mission planning.** No pass prediction, TLE propagation, orbit geometry, visibility windows or tasking schedules.
- **No live availability lookup.** No Copernicus, USGS, commercial provider or weather API calls.
- **No cloud probability modelling.** The tool MAY state that optical data are cloud-sensitive. It MUST NOT predict future cloud availability.
- **No object-detection accuracy prediction.** No Johnson criteria, no pixels-on-target heuristics such as "3 pixels = detection", no target-size arithmetic.
- **No sub-pixel detection claims.**
- **No InSAR pair validation.** Sentinel-1 MAY be identified as SAR capable. The tool MUST NOT claim that two scenes form a usable interferometric pair; coherence, baseline, orbit, geometry and preprocessing are out of scope.
- **No business viability scoring.** No market sizing, ROI, price estimates or customer recommendations.
- **No commercial satellite catalog.** v0.1 contains public reference missions only.
- **No automatic mission ranking or recommendation.**

Deferred to possible future versions, and explicitly not reasons to expand v0.1: commercial VHR missions, hyperspectral, LiDAR, RF sensing, weather satellites, AOI geometry, live acquisition calendars, tasking APIs, cloud climatology, mission recommendation, natural-language compilation, an MCP server, an HTTP API, and any web UI.

---

## 4. Supported missions

v0.1 supports exactly five mission profiles:

| Mission id | Display name | Nominal revisit | Revisit scope | Swath |
| --- | --- | --- | --- | --- |
| `sentinel-2` | Copernicus Sentinel-2 | 5 days | `equator_constellation_nominal` | 290 km |
| `sentinel-1-iw` | Copernicus Sentinel-1 IW | 6 days | `equator_two_satellite_nominal` | 250 km |
| `landsat-8` | Landsat 8 | 16 days | `nominal_repeat_cycle` | 185 km |
| `landsat-9` | Landsat 9 | 16 days | `nominal_repeat_cycle` | 185 km |
| `landsat-8-9` | Landsat 8 + Landsat 9 | 8 days | `nominal_combined_offset` | 185 km |

`sentinel-1-iw` represents the Interferometric Wide swath land-oriented profile only.

`landsat-8-9` represents the combined nominal Landsat 8 + Landsat 9 constellation cadence. It is not a separate spacecraft and MUST NOT be interpreted as simultaneous coverage. Its sensor abstraction is identical to the individual missions.

Adding a mission requires a specification change.

---

## 5. Sensing vocabulary

### 5.1 Modalities

```text
optical_multispectral   thermal_ir   sar_c_band
```

### 5.2 Band families

Band families are deliberate abstractions, not individual instrument bands. Individual band wavelengths are not modelled in v0.1.

The canonical vocabulary order is normative and is used for deterministic iteration (**D-4**):

```text
visible  coastal_aerosol  nir  red_edge  swir
water_vapor  cirrus  panchromatic  thermal_ir  c_band_sar
```

### 5.3 Band family to modality mapping

| Modality | Band families |
| --- | --- |
| `optical_multispectral` | `visible`, `coastal_aerosol`, `nir`, `red_edge`, `swir`, `water_vapor`, `cirrus`, `panchromatic` |
| `thermal_ir` | `thermal_ir` |
| `sar_c_band` | `c_band_sar` |

### 5.4 Output kinds

```text
instrument_measurement  derived_product  model_inference  business_metric
```

### 5.5 Revisit scopes

```text
equator_constellation_nominal
equator_two_satellite_nominal
nominal_repeat_cycle
nominal_combined_offset
```

---

## 6. Mission catalog model

The catalog is packaged static data. The runtime MUST read it locally and MUST NOT fetch, refresh or extend it at runtime.

### 6.1 Mission entry

Each mission entry contains:

```yaml
id:
display_name:
modalities:
nominal_revisit:
  days:
  scope:
swath_km:
default_multispectral_gsd_m:      # optical missions only
night_support:
all_weather:
bands:
source_ids:
modality_inventory_source_ids:
band_inventory_source_ids:
capability_sources:
```

### 6.2 Band entries

An available non-SAR band family carries `available: true` and a positive `resolution_m`. An available SAR family carries `available: true` and a `resolution` mapping with positive `range_m` and `azimuth_m`. An unavailable family carries `available: false`.

A band family absent from a mission's `bands` map MUST be treated as unavailable.

### 6.3 Default multispectral GSD

Every mission with the `optical_multispectral` modality MUST declare `default_multispectral_gsd_m` as explicit catalog data with its own provenance.

This value MUST NOT be derived at runtime — not from band ordering, not from the minimum band resolution, and not from any other computation over the band table. Panchromatic resolution MUST NOT contribute to it.

Normative values:

| Mission | `default_multispectral_gsd_m` |
| --- | --- |
| `sentinel-2` | 10 |
| `landsat-8` | 30 |
| `landsat-9` | 30 |
| `landsat-8-9` | 30 |

A mission without the `optical_multispectral` modality MUST NOT declare this field.

### 6.4 Night support

`night_support` maps keys to one of exactly three values:

```text
true    false    occasional
```

`occasional` means: technically or programmatically possible, but not treated as guaranteed nominal availability.

Resolution for a band family proceeds in this order, and MUST be deterministic:

1. an exact band-family key (for example `thermal_ir`);
2. the family's group key — `reflected_optical`, `thermal_ir` or `c_band_sar` (**D-2**).

There is **no implicit default**. A family whose state cannot be resolved by the chain above is *unstated*.

Night support MUST NOT be inferred as `false` from missing metadata. Missing night-support metadata is a catalog defect, not evidence that a mission lacks a capability. Catalog integrity validation MUST fail if any **available** band family on any mission is unstated (§13).

### 6.5 Provenance model

Every mission capability consumed by a rule MUST cite at least one first-party `source_id`.

Three provenance mechanisms exist:

- **`capability_sources`** — a map from capability key to source id list, covering `modalities`, `nominal_revisit`, `swath_km`, `all_weather`, `night_support`, `default_multispectral_gsd_m` (optical missions only) and `bands.<family>` for every listed family (**D-1**).
- **`modality_inventory_source_ids`** — sources designated authoritative for the mission's **complete** modality inventory.
- **`band_inventory_source_ids`** — sources designated authoritative for the mission's **complete** band inventory.

A finding that concludes a capability is **absent** MUST cite the relevant inventory source list. Generic mission-level provenance MUST NOT be substituted merely to avoid an empty `source_ids` array. Provenance lookup MUST NOT fall back to a wider source set.

### 6.6 Source registry

The catalog MUST ship a source registry containing at minimum these first-party sources:

| Source id | Publisher | Resource |
| --- | --- | --- |
| `esa-sentiwiki-s2-mission` | ESA / Copernicus | Sentinel-2 Mission |
| `esa-s1-facts-and-figures` | ESA | Sentinel-1 Facts and Figures |
| `esa-sentiwiki-s1-mission` | ESA / Copernicus | Sentinel-1 Mission |
| `esa-sentiwiki-s1-products` | ESA / Copernicus | Sentinel-1 Products |
| `usgs-landsat-8` | USGS | Landsat 8 |
| `usgs-landsat-9` | USGS | Landsat 9 |
| `usgs-landsat-acquisition-schedules` | USGS | Landsat acquisition schedules |
| `usgs-landsat-acquisition-plan` | USGS | Landsat 8-9 long term acquisition plan |

Source URLs are **provenance only**. The runtime MUST NOT fetch them.

Acceptable sources are the mission operator's own documentation. Blog posts, aggregators and encyclopedias MUST NOT be used.

### 6.7 SAR resolution

SAR resolution is not physically identical to optical GSD. The engine MUST NOT compare a SAR resolution against an optical GSD requirement, or vice versa.

The nominal SAR resolution used for comparison is the **larger (worse)** of the range and azimuth dimensions. For Sentinel-1 IW this is `max(5, 20) = 20 m`. This is intentionally conservative.

---

## 7. Requirement document

### 7.1 Accepted formats

`.yaml`, `.yml`, `.json`. Format is dispatched by file suffix; any other suffix MUST be rejected as invalid input (**D-16**).

### 7.2 Structure

```yaml
schema_version: "0.1"
name: parking-lot-monitoring
objective: >
  Human-readable metadata only.
candidate_missions:
  - sentinel-2
requirements:
  modality_any_of:
    - optical_multispectral
  spectral_bands_all_of:
    - visible
  spatial:
    optical_max_gsd_m: 10
    thermal_max_gsd_m: 100
    sar_max_resolution_m: 20
  temporal:
    max_nominal_revisit_days: 5
  illumination:
    must_support_night: false
  weather:
    must_support_all_weather: false
  coverage:
    min_single_pass_swath_km: 100
  output:
    kind: model_inference
```

### 7.3 Field rules

| Field | Requirement |
| --- | --- |
| `schema_version` | Required. MUST equal `"0.1"`. |
| `name` | Required string, 1–100 characters. |
| `objective` | Optional string. MUST NEVER be parsed by the rule engine. |
| `candidate_missions` | Optional non-empty list of supported mission ids, interpreted as alternatives. Omitted means: evaluate every mission in the catalog. |
| `requirements.modality_any_of` | Optional non-empty list. At least one listed modality must be available. |
| `requirements.spectral_bands_all_of` | Optional non-empty list. Every listed family must be available. |
| `requirements.spatial.*` | Optional positive numbers. The three fields are independent and never interchangeable. |
| `requirements.temporal.max_nominal_revisit_days` | Optional positive number. |
| `requirements.illumination.must_support_night` | Optional boolean. |
| `requirements.weather.must_support_all_weather` | Optional boolean. |
| `requirements.coverage.min_single_pass_swath_km` | Optional positive number. |
| `requirements.output.kind` | **Required.** One of the four output kinds. |

### 7.4 Input validation behavior

Validation is strict. All of the following MUST be rejected as invalid input:

- **Duplicate mapping keys**, in YAML and in JSON, at any nesting depth. A repeated key makes a document's meaning depend on parser behaviour rather than on what it states, so such a document is ambiguous. Last-value-wins resolution MUST NOT be applied. Duplicate-key rejection MUST also apply to the packaged catalog data (**D-17**).
- **Unknown keys** at any level of the document (**D-12**).
- **Empty lists** for `candidate_missions`, `modality_any_of` or `spectral_bands_all_of`. An empty list is rejected rather than treated as absent (**D-13**).
- **Duplicate values** within any of those lists (**D-14**).
- Values of the wrong type, non-positive numbers where a positive number is required, non-boolean values for boolean fields, an out-of-range `name` length, an unsupported `schema_version`, a missing `output.kind`, an unknown output kind, an unknown modality, an unknown band family, an unknown mission id, an unsupported file suffix, an unreadable file, an empty document, and any parse error.

A requirement referencing a capability the tool does not model MUST be rejected at input-validation time. It MUST NOT be reported as a finding.

Duplicate entries in `candidate_missions` and repeated `--mission` options are collapsed order-preservingly rather than rejected (**D-15**).

Numeric values that are supplied as integers MUST remain integers through validation and into report output (**D-18**).

### 7.5 Parsing safety

YAML MUST be parsed with a safe loader that permits no arbitrary object construction. There MUST be no code execution, template evaluation or shell invocation driven by a requirement document.

### 7.6 Testable requirements

A requirement is **testable** when at least one of the following is present:

- a non-empty `modality_any_of`
- a non-empty `spectral_bands_all_of`
- any `spatial` field
- `temporal.max_nominal_revisit_days`
- `illumination.must_support_night` set to `true`
- `weather.must_support_all_weather` set to `true`
- `coverage.min_single_pass_swath_km`

`must_support_night: false` and `must_support_all_weather: false` are **not** constraints: they can never contradict a mission capability and therefore do not make a requirement testable (**D-9**).

When no testable requirement exists, the engine MUST emit `EFL901` and MUST NOT run any capability rule (**D-10**). `EFL901` is emitted once per mission result (**D-11**).

---

## 8. Rule engine

Each rule MUST be an independent deterministic unit reading nothing except the requirement document and the static catalog. Rules MUST NOT consult a clock, a random source, the environment, the filesystem or the network.

Rule execution order is fixed: modality, spectral, spatial, temporal, illumination, weather, coverage — followed by the output-kind rule, which is applied even when no testable requirement exists.

### 8.1 Modality rule — EFL201

If `modality_any_of` is present and no listed modality is available, emit `EFL201` with effect `FAIL`, citing `modality_inventory_source_ids`.

### 8.2 Spectral rule — EFL202

For each family in `spectral_bands_all_of` that is not available, emit one `EFL202` with effect `FAIL`, citing `band_inventory_source_ids`. Families are iterated in canonical vocabulary order (**D-7**).

### 8.3 Spatial rules — EFL201, EFL301, EFL302, EFL303

Each spatial field implies a modality:

| Field | Implied modality | Unmet code |
| --- | --- | --- |
| `optical_max_gsd_m` | `optical_multispectral` | `EFL301` |
| `thermal_max_gsd_m` | `thermal_ir` | `EFL302` |
| `sar_max_resolution_m` | `sar_c_band` | `EFL303` |

**Absent modality.** If the mission lacks the implied modality, emit `EFL201` with effect `FAIL`, recording the implying field, and citing `modality_inventory_source_ids`. `EFL30x` MUST NOT be used for this case: `EFL30x` means the modality exists but its resolution does not meet the numeric requirement.

**Optical comparison.**

- If `spectral_bands_all_of` names one or more optical families, compare each named family's own resolution and emit one `EFL301` per violating family. A named family that is unavailable is reported by the spectral rule only and produces no `EFL301` (**D-8**). A named `panchromatic` is compared against panchromatic resolution (**D-8a**).
- If no optical family is named, compare against the mission's explicit `default_multispectral_gsd_m`. The resulting finding records `basis: "default_multispectral_gsd_m"` and names no band family, because the default is a mission-level fact.

**Thermal comparison.** Compare against the `thermal_ir` band resolution.

**SAR comparison.** Compare against the larger of the range and azimuth dimensions (§6.7).

A comparison passes when the catalog value is less than or equal to the requirement.

### 8.4 Temporal rules — EFL401, EFL402

If `max_nominal_revisit_days` is present:

- when nominal revisit **exceeds** the requirement, emit `EFL401` with effect `FAIL`;
- otherwise emit `EFL402` with effect **`PASS`**.

`EFL402` is informational. It records that a nominal revisit interval is not equivalent to guaranteed usable observation frequency at a particular location. It MUST always be emitted when a temporal requirement is met, and it MUST NEVER change a verdict.

### 8.5 Illumination rules — EFL501, EFL502

These rules apply only when `must_support_night` is `true`.

**Semantic ranking.** Night support has a total semantic ranking that MUST govern the outcome:

```text
true  >  occasional  >  false
```

`true` produces no finding; `occasional` produces `EFL502` with effect `CONDITIONAL`; `false` produces `EFL501` with effect `FAIL`.

**Selection.** Explicitly requested modality and band constraints always take precedence over fallback family selection:

1. **`spectral_bands_all_of` present** — every named family must work at night. Each named, available family is evaluated independently and each offending family produces its own finding (**D-5**). An explicitly required family MUST NOT be rescued by another family the mission happens to carry.
2. **Only `modality_any_of` present** — candidates are the mission's available families belonging to a listed modality; they are alternatives, so the best-ranked outcome among them wins.
3. **Neither present** — candidates are all of the mission's available families, as alternatives, and the best-ranked outcome wins.

**Tie-breaking.** In the alternatives cases, canonical vocabulary order is used **only** to choose which family to name among candidates that share the winning rank. This ordering is a deterministic presentation and tie-breaking rule only. It MUST NOT override the semantic ranking above, and it MUST NOT override explicitly requested modality or band constraints.

If the candidate set is empty, this rule emits nothing; the modality or spectral rule reports the underlying absence.

Only available families are ever evaluated, and §6.4 guarantees that every available family resolves to an explicit state.

### 8.6 Weather rule — EFL601

If `must_support_all_weather` is `true` and the mission is not all-weather, emit `EFL601` with effect `FAIL`.

"All-weather" means only that the mission does not depend on visible cloud-free conditions the way optical and thermal imaging does. It MUST NOT be presented as implying that SAR is unaffected by every atmospheric or environmental condition.

### 8.7 Coverage rule — EFL701

If `min_single_pass_swath_km` exceeds the mission swath, emit `EFL701` with effect `FAIL`.

Only single-pass width is evaluated. Mosaicking multiple passes MUST NOT be considered.

### 8.8 Output-kind rules — EFL801, EFL802, EFL803

| `output.kind` | Finding | Effect |
| --- | --- | --- |
| `instrument_measurement` | none | — |
| `derived_product` | `EFL801` | `CONDITIONAL` |
| `model_inference` | `EFL802` | `CONDITIONAL` |
| `business_metric` | `EFL803` | `CONDITIONAL` |

`business_metric` MUST NOT be marked `FAIL` automatically: an inference chain may still be possible, it simply cannot be judged from mission specifications. Its explanation MUST state that the output is not directly observable from satellite mission specifications and requires an external inference chain and potentially non-EO data.

These findings depend on no mission capability and therefore carry no `source_ids`.

---

## 9. Reason-code registry

Reason codes are public API. Once released, a code MUST NEVER be reused for a different meaning. If a code's meaning must change, the old code is retired and a new one allocated.

A reason code identifies a finding **type**, not a unique finding instance. The same code MAY appear several times in one mission result when several independent requirements produce the same type of finding. Each such finding MUST carry enough `required` and `capability` detail to be distinguished from its siblings, and ordering MUST remain deterministic.

v0.1 reserves no unused codes. Every code below is reachable by some rule.

| Code | Name | Category | Effect |
| --- | --- | --- | --- |
| `EFL201` | `REQUIRED_MODALITY_UNAVAILABLE` | Modality / Spectral | `FAIL` |
| `EFL202` | `REQUIRED_BAND_UNAVAILABLE` | Modality / Spectral | `FAIL` |
| `EFL301` | `OPTICAL_GSD_REQUIREMENT_UNMET` | Spatial | `FAIL` |
| `EFL302` | `THERMAL_GSD_REQUIREMENT_UNMET` | Spatial | `FAIL` |
| `EFL303` | `SAR_RESOLUTION_REQUIREMENT_UNMET` | Spatial | `FAIL` |
| `EFL401` | `NOMINAL_REVISIT_TOO_SLOW` | Temporal | `FAIL` |
| `EFL402` | `NOMINAL_REVISIT_NOT_AVAILABILITY_GUARANTEE` | Temporal | `PASS` (informational) |
| `EFL501` | `NIGHT_OPERATION_UNAVAILABLE` | Illumination | `FAIL` |
| `EFL502` | `NIGHT_OPERATION_CONDITIONAL` | Illumination | `CONDITIONAL` |
| `EFL601` | `ALL_WEATHER_REQUIREMENT_UNMET` | Weather | `FAIL` |
| `EFL701` | `SINGLE_PASS_SWATH_REQUIREMENT_UNMET` | Coverage | `FAIL` |
| `EFL801` | `DERIVED_PROCESSING_REQUIRED` | Output / Inference | `CONDITIONAL` |
| `EFL802` | `MODEL_VALIDATION_REQUIRED` | Output / Inference | `CONDITIONAL` |
| `EFL803` | `BUSINESS_METRIC_INFERENCE_REQUIRED` | Output / Inference | `CONDITIONAL` |
| `EFL901` | `NO_TESTABLE_REQUIREMENTS` | Knowledge Limit | `UNKNOWN` |

### 9.1 Retired code

`EFL902 CAPABILITY_NOT_MODELED` was defined during specification drafting and **removed before release**. It was unreachable: the requirement schema rejects unsupported and unmodelled properties during input validation (§7.4), so no rule could ever emit it. Because v0.1.0 had not been released, removal does not violate reason-code stability.

An implementation MUST NOT emit, reserve or display `EFL902` in v0.1. A future version needing to report an unmodelled capability at runtime MUST allocate a new code rather than revive this one.

---

## 10. Finding structure

Every finding MUST contain exactly these fields:

```json
{
  "code": "EFL401",
  "effect": "FAIL",
  "title": "Nominal revisit requirement unmet",
  "message": "...",
  "required": {},
  "capability": {},
  "source_ids": []
}
```

`source_ids` MUST be non-empty for every finding that depends on a mission capability. It MUST be empty for findings that depend on no mission capability — that is, `EFL801`, `EFL802`, `EFL803` and `EFL901`.

Multiple `EFL201` findings MAY occur for one mission — one from `modality_any_of` and one per implying spatial field — with distinct payloads and no de-duplication (**D-6**).

---

## 11. Deterministic ordering

- **Mission result order** — explicit input order when candidates are supplied (from `--mission` if given, otherwise `candidate_missions`); otherwise catalog order.
- **Finding order** — ascending reason code, then a stable serialization of `required`, then a stable serialization of `capability` (**D-33**). This tie-break makes repeated codes order-stable.
- **JSON property order** — fixed and stable.

---

## 12. Output

### 12.1 JSON report

JSON is the v0.1 agent interface.

```json
{
  "schema_version": "0.1",
  "ruleset_version": "0.1.0",
  "catalog_version": "2026-08-15.1",
  "requirement": { "name": "parking-lot-monitoring" },
  "portfolio_verdict": "FAIL",
  "mission_results": [
    { "mission_id": "sentinel-2", "verdict": "FAIL", "findings": [] }
  ]
}
```

JSON output MUST NOT contain a current timestamp, machine hostname, username, filesystem path or random identifier, unless such a value was explicitly part of user input.

`objective` is validated and retained in memory but MUST NOT appear in the JSON report (**D-30**).

Serialization uses two-space indentation, non-escaped non-ASCII output, and a trailing newline (**D-29**).

### 12.2 Text report

The text report is human-facing. Its exact layout is implementation-defined within the following normative constraints (**D-24** through **D-27**):

- It MUST state the requirement name, ruleset version and catalog version.
- For each mission it MUST state the mission id and verdict, and for each finding the reason code, effect, an explanation, and the source ids behind the cited capability.
- It MUST render the `required` and `capability` payloads in human-readable form.
- It MUST state the portfolio verdict after the mission results.
- It MUST close with a scope notice stating that `PASS` is not a guarantee that a real EO project will succeed, and naming what was not evaluated. The notice follows the portfolio verdict.

The closing scope notice is **informational only**. It MUST NOT affect any verdict, MUST NOT appear as a finding, and MUST NOT appear in JSON output.

Full source URLs are printed by `show-mission`; findings cite source ids (**D-26**).

---

## 13. Catalog integrity requirements

Catalog integrity validation MUST run whenever the catalog is loaded, and CI MUST fail when any of the following holds:

- a mission has no `source_ids`
- a mission has no `modality_inventory_source_ids` or no `band_inventory_source_ids`
- any source reference names an unknown source
- a capability consumed by a rule has no `source_ids`
- a duplicate mission id exists
- a duplicate source id exists
- a duplicate reason code exists
- an unknown band family or unknown modality exists
- an unknown revisit scope exists
- an invalid or non-positive revisit value exists
- a non-positive swath exists
- a non-positive band resolution or SAR dimension exists
- an invalid `night_support` value or unknown `night_support` key exists
- **an available band family has no resolvable night-support state**
- **an optical mission has no `default_multispectral_gsd_m`, or it is non-positive**
- **a non-optical mission declares `default_multispectral_gsd_m`**
- `capability_sources` contains an unused key

A catalog integrity failure is an internal tool failure, not a feasibility finding (§14.2).

---

## 14. Command line interface

### 14.1 Commands

```bash
eo-feasibility-lint check FILE
eo-feasibility-lint list-missions
eo-feasibility-lint show-mission MISSION_ID
eo-feasibility-lint rules
```

`check` options:

| Option | Behavior |
| --- | --- |
| `--mission MISSION_ID` | Repeatable. Overrides `candidate_missions` from the file. |
| `--format text\|json` | Default `text`. |
| `--fail-on fail\|unknown\|conditional` | Default `fail`. |

A `--version` option MAY be provided; it prints the ruleset version (**D-22**). Invocation as a Python module MAY be supported in addition to the console script (**D-23**).

The output format of `list-missions`, `show-mission` and `rules` is implementation-defined (**D-28**). `show-mission` MUST print the mission's capabilities, per-family night support, `default_multispectral_gsd_m` where applicable, and its source URLs, and MUST state that those sources are provenance only.

### 14.2 Exit codes

```text
0 = result below the configured fail threshold
1 = configured feasibility threshold reached
2 = invalid input or CLI usage
3 = internal tool failure
```

An internal bug MUST NEVER masquerade as a feasibility finding. Catalog integrity failures and unexpected exceptions MUST exit `3` with a diagnostic on standard error (**D-21**).

Exit code `1` is determined by the **portfolio** verdict, not by any individual mission verdict (**D-19**).

The threshold comparison is `severity(portfolio_verdict) >= severity(threshold)`. Therefore `--fail-on conditional` also exits `1` on `UNKNOWN` and `FAIL`, and `--fail-on unknown` also exits `1` on `FAIL` (**D-20**).

---

## 15. Determinism requirements

An implementation MUST guarantee that identical input, catalog version and ruleset version produce byte-identical output:

- within one process across repeated invocations;
- across separate processes;
- across differing hash seeds and iteration-order conditions.

The runtime MUST NOT consult a clock or any random source. It MUST NOT import date, time, random, uuid or secrets facilities.

Reports MUST be free of ISO timestamps, absolute filesystem paths, hostnames, usernames and random identifiers.

---

## 16. Privacy, network and security requirements

The runtime MUST:

- make no network requests of any kind;
- collect no telemetry or analytics;
- upload no requirement data;
- read no API keys, tokens or credentials;
- perform all checking locally.

The runtime MUST NOT import an HTTP client or socket facility.

YAML MUST use safe parsing with no arbitrary object construction. There MUST be no code execution, template evaluation or shell invocation derived from input. Duplicate mapping keys MUST be rejected (§7.4).

Source URLs are provenance metadata and MUST NOT be treated as endpoints.

---

## 17. Implementation constraints

- **Language:** Python 3.11+. CI MUST cover 3.11, 3.12 and 3.13.
- **Runtime dependencies:** PyYAML only. `requests`, `httpx`, LLM SDKs, `pandas`, `numpy` and any other runtime dependency MUST NOT be added without a specification change.
- **Development dependencies:** `pytest` and `ruff`.
- **Schema validation:** runtime validation is hand-written; a JSON Schema library MUST NOT be added in v0.1. The published JSON Schema files and the runtime validator MUST be kept synchronized by tests, and CI MUST fail if they disagree.
- **Architecture:** requirement loader → schema validator → catalog loader → rule engine → mission results → portfolio aggregator → renderer.
- **CI:** MUST run on push and pull request, execute `ruff check .` and `pytest`, perform an installed-CLI smoke test, and pin GitHub Actions to immutable commit SHAs. CI MUST NOT require secrets.
- **License:** Apache License 2.0.

---

## 18. Accepted implementation decisions

The following decisions were reviewed and accepted at release freeze. They are normative for v0.1.0. Where a decision is elaborated in an earlier section, that section governs the detail.

**Catalog structure and provenance**

- **D-1** — The `capability_sources` map is the mechanism satisfying the per-capability provenance requirement; its key naming is normative (§6.5).
- **D-2** — Night-support group keys (`reflected_optical`, `thermal_ir`, `c_band_sar`) and the two-step resolution order are normative (§6.4).
- **D-3** — Landsat profiles state `coastal_aerosol: false` and `cirrus: false` explicitly. These families are available reflected-solar bands and were previously covered only by an implicit default; explicit statement is required by §6.4.
- **D-4** — The canonical band-family vocabulary order (§5.2) is load-bearing for deterministic iteration, illumination tie-breaking and catalog display.

**Rule semantics**

- **D-5** — Illumination finding granularity: all-of selection emits one finding per offending family; alternatives selection emits a single finding naming a representative family plus the full evaluated candidate list (§8.5).
- **D-6** — Multiple `EFL201` findings may occur for one mission with distinct payloads and no de-duplication (§10).
- **D-7** — The spectral rule iterates band families in canonical vocabulary order.
- **D-8** — An explicitly required optical family that is unavailable produces only `EFL202`, never also `EFL301`. The illumination rule likewise skips unavailable families already reported by the spectral rule.
- **D-8a** — An explicitly named `panchromatic` family is compared against panchromatic resolution.
- **D-9** — `must_support_night: false` and `must_support_all_weather: false` are not testable requirements (§7.6).
- **D-9.1** — Every text report carries the closing scope notice (§12.2).
- **D-10** — When no testable requirement exists, capability rules are skipped entirely; only `EFL901` plus any output-kind finding are emitted.
- **D-11** — `EFL901` is emitted once per mission result, not once per report.

**Input validation**

- **D-12** — Unknown keys anywhere in the document are rejected.
- **D-13** — Empty lists are rejected rather than treated as absent.
- **D-14** — Duplicate values within a list are rejected.
- **D-15** — Duplicate `candidate_missions` entries and repeated `--mission` options are collapsed order-preservingly.
- **D-16** — Format dispatch is by file suffix; other suffixes are rejected.
- **D-17** — Duplicate-key rejection applies to JSON input and to the packaged catalog as well as to requirement YAML.
- **D-18** — Integers survive validation as integers into report output.

**CLI and exit behavior**

- **D-19** — Exit code `1` is driven by the portfolio verdict.
- **D-20** — `--fail-on` compares severity `>=` threshold.
- **D-21** — Catalog integrity failure and unexpected exceptions map to exit `3`.
- **D-22** — A `--version` option is provided.
- **D-23** — Module-form invocation is supported alongside the console script.

**Output formatting**

- **D-24** — Text report layout, including mission underlining and line wrapping, is implementation-defined within §12.2.
- **D-25** — Per-code human phrasing of `required` and `capability`, including revisit-scope prose, is implementation-defined.
- **D-26** — Findings cite source ids; full URLs appear in `show-mission`.
- **D-27** — `show-mission` prints `default_multispectral_gsd_m` where applicable.
- **D-28** — `list-missions`, `show-mission` and `rules` output formats are implementation-defined.
- **D-29** — JSON uses two-space indentation, non-escaped non-ASCII output and a trailing newline.
- **D-30** — `objective` is retained but never emitted into the JSON report.

**Repository structure**

- **D-31** — Test support files and a rules package initializer may exist beyond the minimum required file list.
- **D-32** — The strict safe loader is shared between the requirement loader and the catalog loader rather than living in a separate module.

**Ordering**

- **D-33** — The finding tie-break beyond reason code is a stable serialization of `required` then `capability` (§11).

---

## 19. Mandatory test cases

A conforming implementation MUST pass all sixteen cases below. They MUST be maintained in specification order and traceable to these numbers.

| # | Scenario | Expected |
| --- | --- | --- |
| 1 | Sentinel-2; visible; ≤10 m; ≤5 day revisit; daytime; `instrument_measurement` | `PASS` |
| 2 | Sentinel-2 + thermal band | `FAIL`, `EFL202` |
| 3 | Sentinel-2 + all-weather | `FAIL`, `EFL601` |
| 4 | Sentinel-2 + night | `FAIL`, `EFL501` |
| 5 | Sentinel-2 + ≤1 day revisit | `FAIL`, `EFL401` |
| 6 | Sentinel-1 IW; C-band SAR; all-weather; night; ≤20 m SAR; ≤6 day revisit; `instrument_measurement` | `PASS` |
| 7 | Sentinel-1 IW + ≥300 km single-pass swath | `FAIL`, `EFL701` |
| 8 | Landsat 8; visible ≤30 m; ≤16 day revisit | `PASS` |
| 9 | Landsat 8; visible ≤10 m | `FAIL`, `EFL301` |
| 10 | Landsat thermal + night | `CONDITIONAL`, `EFL502` |
| 11 | Landsat 8+9; ≤8 day revisit | temporally compatible |
| 12 | Landsat 8+9; ≤5 day revisit | `FAIL`, `EFL401` |
| 13 | Otherwise valid mission; `model_inference` | at least `CONDITIONAL`, `EFL802` |
| 14 | Any mission; `business_metric` | at least `CONDITIONAL`, `EFL803` |
| 15 | No meaningful technical constraint | `UNKNOWN`, `EFL901` |
| 16 | Same input executed twice | byte-identical JSON |

In cases 1, 6, 8 and 11 the temporal requirement is met, so `EFL402` is present as an informational finding and the verdict remains `PASS`.

Beyond these, the test suite MUST cover: each rule in isolation, catalog integrity violations, provenance completeness for every capability-dependent reason code, duplicate-key rejection, verdict precedence and portfolio aggregation, CLI exit codes, and determinism across processes and hash seeds.

---

## 20. Definition of done

v0.1.0 is releasable only when all of the following hold:

- `pytest` green
- `ruff check .` green
- all sixteen mandatory cases green
- catalog integrity green
- installed-CLI smoke test green
- documented quick start verified
- no secrets present
- no network access at runtime

And when a new user can install the package, run the linter against the impossible-thermal example, and within approximately five minutes understand:

1. that the requirement failed;
2. why it failed;
3. which technical constraint caused it;
4. which first-party mission specification supports that conclusion;
5. what the tool did **not** evaluate.

---

## 21. Change control

An implementation MUST NOT, without a specification change, add missions, add or repurpose reason codes, change verdict semantics or thresholds, invent EO heuristics, introduce AI, introduce network access, introduce telemetry, add runtime dependencies, implement automatic recommendations, change the requirement or report schemas, or broaden scope.

If implementation reveals a contradiction within this specification, work MUST stop and the contradiction MUST be reported as a **SPEC BLOCKER** identifying the conflicting sections, the technical reason they cannot both hold, and a minimal proposed resolution.

---

## 22. Core philosophy

`eo-feasibility-lint` does not attempt to know everything. Its job is narrower:

> Reject what can be rejected from explicit requirements and documented EO capabilities, explain the reason, and say `UNKNOWN` when evidence is insufficient.

That behavior is a feature, not a limitation.
