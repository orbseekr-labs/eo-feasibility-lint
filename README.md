# eo-feasibility-lint

A deterministic, offline command-line linter that checks whether explicit Earth observation requirements contradict known satellite mission capabilities.

It is closer to ESLint or a type checker than to an assistant: no LLM, no network, no probability, no hidden heuristics. Same input plus same catalog and ruleset versions, same answer, every time.

---

## 30-second example

```yaml
# impossible-thermal-sentinel2.yaml
schema_version: "0.1"
name: impossible-thermal-sentinel2

candidate_missions:
  - sentinel-2

requirements:
  modality_any_of:
    - thermal_ir
  spectral_bands_all_of:
    - thermal_ir
  output:
    kind: instrument_measurement
```

```console
$ eo-feasibility-lint check examples/impossible-thermal-sentinel2.yaml
```

```text
EO FEASIBILITY LINT

Requirement:
impossible-thermal-sentinel2

Ruleset:
0.1.0

Catalog:
2026-08-15.1

sentinel-2
------------

Verdict: FAIL

EFL201 FAIL
Required modality unavailable.
The mission provides none of the required sensing modalities.

Required:
any of: thermal_ir

Catalog:
mission modalities: optical_multispectral

Sources:
esa-sentiwiki-s2-mission

EFL202 FAIL
Required spectral band family unavailable.
The mission does not provide the thermal_ir band family.

Required:
band family: thermal_ir

Catalog:
thermal_ir not available

Sources:
esa-sentiwiki-s2-mission

Portfolio verdict:
FAIL

PASS is not a guarantee that a real EO project will succeed. Only the explicit
requirements above were checked, against a static mission catalog. Acquisition,
cloud cover, image quality, model accuracy, detection accuracy, tasking
availability and revisit at a specific location were not evaluated.
```

Sentinel-2 carries no thermal infrared instrument. That is a documented fact, not a guess: the report names the reason code, the requirement that triggered it, the catalog value it contradicts, and the first-party source behind that value. Exit code `1`.

---

## Installation

Python 3.11 or newer.

```bash
pip install .
```

The only runtime dependency is PyYAML.

---

## Quick start

```bash
# check a requirement file
eo-feasibility-lint check examples/sentinel2-ndvi.yaml

# restrict to specific missions, overriding the file
eo-feasibility-lint check requirement.yaml --mission sentinel-1-iw --mission landsat-8

# machine-readable output
eo-feasibility-lint check requirement.yaml --format json

# treat anything short of a clean pass as a failure
eo-feasibility-lint check requirement.yaml --fail-on conditional

# browse the catalog and the rules
eo-feasibility-lint list-missions
eo-feasibility-lint show-mission sentinel-1-iw
eo-feasibility-lint rules
```

Exit codes:

| Code | Meaning |
| --- | --- |
| `0` | result below the configured fail threshold |
| `1` | configured feasibility threshold reached |
| `2` | invalid input or CLI usage |
| `3` | internal tool failure |

An internal bug never masquerades as a feasibility finding.

---

## What the verdicts mean

**`PASS`** — every explicit requirement that v0.1 knows how to evaluate is compatible with the mission, and nothing conditional or unknown remains.

> **PASS is not a guarantee that a real EO project will succeed.**
>
> It does not promise image acquisition, clear skies, image quality, model accuracy, detection accuracy, ground-truth validity, tasking availability, revisit at your exact coordinate, usable SAR coherence, economic viability, or any commercial outcome.

**`CONDITIONAL`** — no hard contradiction, but success depends on something outside the static catalog: processing, a validated model, a non-guaranteed acquisition mode, or scheduling.

**`UNKNOWN`** — the tool cannot decide, because the requirement is not specific enough or depends on something v0.1 does not model. A requirement with no technical constraints returns `UNKNOWN`, never a meaningless `PASS`.

**`FAIL`** — at least one explicit requirement directly contradicts a documented mission capability.

Per mission the worst finding wins: `FAIL > UNKNOWN > CONDITIONAL > PASS`.

Candidate missions are alternatives, so the portfolio verdict asks whether *at least one* candidate is viable: `PASS > CONDITIONAL > UNKNOWN > FAIL`. A portfolio `PASS` means one candidate passed, not that all of them did.

---

## Supported missions

| Mission id | Profile | Nominal revisit | Swath |
| --- | --- | --- | --- |
| `sentinel-2` | Copernicus Sentinel-2 | 5 days | 290 km |
| `sentinel-1-iw` | Copernicus Sentinel-1, Interferometric Wide swath only | 6 days | 250 km |
| `landsat-8` | Landsat 8 | 16 days | 185 km |
| `landsat-9` | Landsat 9 | 16 days | 185 km |
| `landsat-8-9` | Combined Landsat 8 + 9 cadence | 8 days | 185 km |

`landsat-8-9` is a constellation cadence, not a spacecraft, and does not imply simultaneous coverage. Run `eo-feasibility-lint show-mission <id>` for the full catalog entry, including per-band resolutions and night support.

v0.1 contains public reference missions only. There is no commercial satellite catalog.

---

## What gets checked

| Requirement | Checked against |
| --- | --- |
| `modality_any_of` | mission modalities |
| `spectral_bands_all_of` | band-family availability |
| `spatial.optical_max_gsd_m` | optical GSD of the required families, or the mission's catalogued default multispectral GSD |
| `spatial.thermal_max_gsd_m` | thermal GSD |
| `spatial.sar_max_resolution_m` | the larger (worse) nominal SAR dimension |
| `temporal.max_nominal_revisit_days` | nominal revisit interval |
| `illumination.must_support_night` | night support of the required capability |
| `weather.must_support_all_weather` | dependence on cloud-free conditions |
| `coverage.min_single_pass_swath_km` | single-pass swath width |
| `output.kind` | what the requested output implies |

Band families are deliberate abstractions (`visible`, `nir`, `red_edge`, `swir`, `thermal_ir`, `c_band_sar`, …), not individual instrument bands.

Optical GSD, thermal GSD and SAR resolution are three separate fields and are never compared with one another. SAR resolution is not physically the same measurement as optical GSD.

A few rules worth knowing:

- When an optical GSD requirement names no spectral family, the mission's explicit `default_multispectral_gsd_m` catalog field applies — 10 m for Sentinel-2, 30 m for Landsat. This is catalog data with its own provenance, never inferred from band ordering or from the finest band. Panchromatic never substitutes for the multispectral capability, so Landsat resolves against 30 m, not 15 m.
- SAR comparison uses the worse nominal dimension — `max(5 m range, 20 m azimuth) = 20 m` for Sentinel-1 IW. This is intentionally conservative.
- A spatial requirement for a sensor the mission does not carry is reported as `EFL201` (modality unavailable), because the requirement implies that modality.
- Only single-pass swath width is evaluated. Mosaicking several passes is not.
- `EFL402` is informational: it records that nominal revisit is not a guarantee of usable observation frequency, and never changes a verdict.

---

## What does NOT get checked

This list is the point of the tool, not a disclaimer.

- **No natural-language requirement extraction.** "I want to measure parking lot traffic every day" is never converted into technical requirements. `objective` is human-readable metadata and is never parsed.
- **No mission planning.** No pass prediction, TLE propagation, orbit geometry, visibility windows or tasking schedules.
- **No live availability lookup.** No Copernicus, USGS, commercial provider or weather APIs — at any time, for any reason.
- **No cloud probability modelling.** The tool can say optical data are cloud-sensitive. It cannot tell you whether next Tuesday is clear.
- **No object-detection accuracy prediction.** No Johnson criteria, no "3 pixels means detection" heuristic, no target-size arithmetic.
- **No sub-pixel claims.**
- **No InSAR pair validation.** Sentinel-1 is identified as SAR capable. Whether two scenes form a usable interferometric pair — coherence, baseline, orbit, geometry, preprocessing — is out of scope.
- **No business viability scoring.** No market sizing, ROI, pricing or customer advice.
- **No mission ranking or recommendation.** The tool reports technical results. It never tells you which satellite is best.
- **No commercial satellite catalog.**

---

## Reason codes

Reason codes are public API. Once released, a code is never reused for a different meaning.

| Code | Name | Effect |
| --- | --- | --- |
| `EFL201` | `REQUIRED_MODALITY_UNAVAILABLE` | FAIL |
| `EFL202` | `REQUIRED_BAND_UNAVAILABLE` | FAIL |
| `EFL301` | `OPTICAL_GSD_REQUIREMENT_UNMET` | FAIL |
| `EFL302` | `THERMAL_GSD_REQUIREMENT_UNMET` | FAIL |
| `EFL303` | `SAR_RESOLUTION_REQUIREMENT_UNMET` | FAIL |
| `EFL401` | `NOMINAL_REVISIT_TOO_SLOW` | FAIL |
| `EFL402` | `NOMINAL_REVISIT_NOT_AVAILABILITY_GUARANTEE` | PASS (informational) |
| `EFL501` | `NIGHT_OPERATION_UNAVAILABLE` | FAIL |
| `EFL502` | `NIGHT_OPERATION_CONDITIONAL` | CONDITIONAL |
| `EFL601` | `ALL_WEATHER_REQUIREMENT_UNMET` | FAIL |
| `EFL701` | `SINGLE_PASS_SWATH_REQUIREMENT_UNMET` | FAIL |
| `EFL801` | `DERIVED_PROCESSING_REQUIRED` | CONDITIONAL |
| `EFL802` | `MODEL_VALIDATION_REQUIRED` | CONDITIONAL |
| `EFL803` | `BUSINESS_METRIC_INFERENCE_REQUIRED` | CONDITIONAL |
| `EFL901` | `NO_TESTABLE_REQUIREMENTS` | UNKNOWN |

`eo-feasibility-lint rules` prints this list with explanations. Every code in the set is reachable; v0.1 reserves no unused codes.

**A reason code identifies a finding *type*, not a unique finding instance.** The same code may legitimately appear several times in one mission result when several independent requirements produce the same type of finding — for example, three required band families that the mission lacks produce three `EFL202` findings. Each carries its own `required` and `capability` detail so they can be told apart, and their order is deterministic (ascending code, then a stable payload key).

---

## JSON output and AI-agent usage

JSON mode is the v0.1 agent interface. There is no MCP server, HTTP API or plugin.

```bash
eo-feasibility-lint check requirement.yaml --format json
```

```json
{
  "schema_version": "0.1",
  "ruleset_version": "0.1.0",
  "catalog_version": "2026-08-15.1",
  "requirement": { "name": "retail-site-revenue" },
  "portfolio_verdict": "CONDITIONAL",
  "mission_results": [
    {
      "mission_id": "sentinel-2",
      "verdict": "CONDITIONAL",
      "findings": [
        {
          "code": "EFL803",
          "effect": "CONDITIONAL",
          "title": "Business metric inference required",
          "message": "The requested output is not directly observable from satellite mission specifications and requires an external inference chain and potentially non-EO data.",
          "required": { "output_kind": "business_metric" },
          "capability": {},
          "source_ids": []
        }
      ]
    }
  ]
}
```

Guarantees an agent can rely on:

- Property order is stable; mission results follow input order, or catalog order when no candidates were given; findings are ordered by ascending reason code.
- The report contains no timestamp, hostname, username, filesystem path or random id, so two runs are byte-identical.
- `source_ids` is non-empty for every finding that depends on a mission capability.
- The full contract is published in [`schemas/report.schema.json`](schemas/report.schema.json); the input contract is in [`schemas/requirement.schema.json`](schemas/requirement.schema.json).

An agent may call this tool. AI is not part of the decision engine.

---

## Data provenance

Every mission fact comes from a first-party mission source, recorded in [`src/eo_feasibility_lint/data/sources.yaml`](src/eo_feasibility_lint/data/sources.yaml) and cited per capability. Findings carry the `source_ids` behind the capability they used, and `show-mission` prints the URLs.

Findings that conclude a capability is *absent* ("Sentinel-2 has no thermal band") cite a source the catalog explicitly designates as authoritative for that mission's complete modality or band inventory, via `modality_inventory_source_ids` and `band_inventory_source_ids`. There is no generic fallback: provenance is never widened just to avoid an empty `source_ids` array, and catalog integrity validation enforces this.

Catalog baseline: **2026-08-15**, catalog version **2026-08-15.1**.

| Source | Publisher |
| --- | --- |
| [Sentinel-2 mission](https://sentiwiki.copernicus.eu/web/s2-mission) | ESA / Copernicus |
| [Sentinel-1 facts and figures](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Facts_and_figures) | ESA |
| [Sentinel-1 mission](https://sentiwiki.copernicus.eu/web/s1-mission) | ESA / Copernicus |
| [Sentinel-1 products](https://sentiwiki.copernicus.eu/web/s1-products) | ESA / Copernicus |
| [Landsat 8](https://www.usgs.gov/landsat-missions/landsat-8) | USGS |
| [Landsat 9](https://www.usgs.gov/landsat-missions/landsat-9) | USGS |
| [Landsat acquisition schedules](https://www.usgs.gov/faqs/what-are-acquisition-schedules-landsat-satellites) | USGS |
| [Landsat 8-9 long term acquisition plan](https://www.usgs.gov/data/landsat-89-long-term-acquisition-plan-earths-continental-landmasses-and-near-shore-coastal) | USGS |

These URLs are provenance only. **The runtime never fetches them.**

---

## Privacy

Everything happens locally:

- no telemetry
- no analytics
- no network requests
- no requirement upload
- no API keys

Your requirement files never leave your machine.

Requirement documents are parsed with a `yaml.SafeLoader` subclass. Duplicate mapping keys are rejected rather than silently resolved last-value-wins, in both YAML and JSON, so an ambiguous document can never be misinterpreted:

```yaml
temporal:
  max_nominal_revisit_days: 5
  max_nominal_revisit_days: 10   # rejected: exit code 2
```

---

## Limitations

- The catalog is a snapshot. Mission capabilities and constellation cadence change; the catalog version tells you which snapshot produced a report.
- Capabilities are abstracted into band families. Individual band wavelengths are not modelled.
- Nominal revisit is a constellation-level number at a stated scope. It is not the revisit at your area of interest, and it says nothing about whether an acquisition was scheduled or usable.
- "All-weather" means only that the mission does not depend on visible cloud-free conditions the way optical and thermal imaging does. SAR is not immune to every atmospheric or environmental condition.
- Only the Sentinel-1 Interferometric Wide swath profile is represented.
- Requirements referencing capabilities the tool does not model are rejected at input-validation time (exit code 2), not reported as a finding.
- A `PASS` reflects the requirements you wrote down. Requirements you did not write down are not evaluated.

Explicitly not in v0.1, and not reasons to expand it: commercial VHR missions, hyperspectral, LiDAR, RF sensing, weather satellites, AOI geometry, live acquisition calendars, tasking APIs, cloud climatology, mission recommendation, natural-language compilation, an MCP server, or a web UI.

---

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

ruff check .
pytest
```

The mission catalog is validated on every load; CI fails on a missing source, a duplicate id, an unknown band family or an invalid capability value. The 16 mandatory specification cases live in [`tests/test_mandatory_cases.py`](tests/test_mandatory_cases.py).

[SPECIFICATION.md](SPECIFICATION.md) is the authoritative normative specification for v0.1.0 — verdict semantics, the catalog model, every rule, the reason-code registry, determinism and provenance requirements, and the accepted implementation decisions. Where this README and the specification differ, the specification governs.

See [CONTRIBUTING.md](CONTRIBUTING.md) before adding a mission, a rule or a reason code — the v0.1 design is frozen, and several tempting changes are deliberately out of scope.

---

## License

[Apache License 2.0](LICENSE).
