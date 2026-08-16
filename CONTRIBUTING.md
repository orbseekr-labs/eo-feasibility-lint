# Contributing

Thanks for your interest. Please read this before opening a pull request — the v0.1 design is deliberately frozen, and several changes that look like obvious improvements are out of scope on purpose.

[SPECIFICATION.md](SPECIFICATION.md) is the authoritative normative specification. This document summarises the parts contributors hit most often; where the two differ, the specification governs.

## The design principle

> Reject what can be rejected from explicit requirements and documented EO capabilities, explain the reason, and say `UNKNOWN` when evidence is insufficient.

Narrow scope is a feature. A tool that answers fewer questions confidently is more useful here than one that answers every question vaguely.

## Non-negotiable properties

Every change must preserve all of these:

- **Deterministic.** Same input plus same catalog and ruleset versions, same bytes out. No clocks, no randomness, no hash-order dependence, no environment data in reports.
- **Offline.** No network calls at runtime, ever. Source URLs are provenance, not endpoints.
- **Zero-token.** No LLM, no probabilistic judgement.
- **Explainable.** Every finding names a reason code, the requirement that triggered it, the catalog value it contradicts, and the first-party source behind that value.
- **Safe.** A `yaml.SafeLoader` subclass only, which additionally rejects duplicate mapping keys. No object construction, template evaluation or shell invocation driven by a requirement document.

## What v0.1 will not accept

Pull requests doing any of these will be closed with a pointer back to this section:

- adding missions, reason codes or requirement fields
- changing verdict semantics, precedence or thresholds
- inventing EO heuristics (Johnson criteria, pixels-on-target, sub-pixel detection, InSAR pair validity, cloud probability)
- adding AI, network access or telemetry
- adding runtime dependencies beyond PyYAML
- automatic mission ranking or recommendation
- natural-language requirement extraction
- broadening scope or redesigning the architecture

Bug fixes, clearer messages, better tests, documentation and catalog corrections backed by first-party sources are all welcome.

## Reason codes are public API

Once released, a reason code is **never** reused for a different meaning. If a code's meaning must change, the old code is retired and a new one is allocated.

A code identifies a finding **type**, not a unique finding instance. The same code may appear several times in one mission result when several independent requirements produce the same type of finding. Each finding must carry enough `required` and `capability` detail to be distinguished from its siblings, and ordering must stay deterministic.

v0.1 reserves no unused codes: every code in the registry is reachable by some rule. If a future version needs to report an unmodelled capability at runtime, it allocates a new code rather than reviving a retired one.

## Catalog changes

Mission facts live in `src/eo_feasibility_lint/data/missions.yaml`, sources in `sources.yaml`.

Every capability a rule consumes must cite at least one first-party source id via `capability_sources`. CI fails on a mission without sources, a capability without sources, a duplicate mission or source id, an unknown band family, an invalid revisit value, a non-positive swath or resolution, or a duplicated reason code.

Three further catalog invariants are enforced:

- **`default_multispectral_gsd_m` is explicit data.** Every mission with an optical multispectral payload states it, with its own provenance. It is never derived from band ordering or from the finest available band, and panchromatic never contributes to it. Missions without an optical payload must not have it.
- **Night support is never implicitly false.** Every *available* band family must resolve to `true`, `false` or `occasional`, either through its own key or through a group key (`reflected_optical`, `thermal_ir`, `c_band_sar`). Missing night-support metadata is a catalog defect, not evidence that a mission lacks the capability, and validation fails on it.
- **Absence needs its own provenance.** `modality_inventory_source_ids` and `band_inventory_source_ids` designate the sources authoritative for a mission's *complete* modality and band inventory. Findings that conclude a capability is absent cite those. Generic mission-level provenance is never substituted to avoid an empty `source_ids`.

Acceptable sources are the mission operator's own documentation (ESA/Copernicus, USGS). Blog posts, aggregator sites and encyclopedias are not.

If a catalog fact changes, bump `catalog_version` in `missions.yaml`. Reports record the version they were produced with, so a stale report stays interpretable.

## Adding or changing a rule

Rules live in `src/eo_feasibility_lint/rules/` and each one exposes `evaluate(requirement, mission) -> list[Finding]`. A rule reads nothing except the requirement document and the mission catalog. Keep them independent — the engine handles ordering and precedence, not the rules.

Findings must carry non-empty `source_ids` whenever they depend on a mission capability. Findings that depend on no capability (the output-kind and no-testable-requirements codes) carry none.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

ruff check .
pytest
```

Tests are organised per rule, plus `tests/test_mandatory_cases.py` (the 16 specification cases, in specification order), `tests/test_catalog.py` (integrity) and `tests/test_determinism.py`.

Add a test alongside any behaviour change. Priority order when they conflict:

```text
Specification > Tests > Implementation > Convenience
```

## Found a contradiction in the specification?

Stop and open an issue titled `SPEC BLOCKER` containing:

1. the exact conflicting specification sections
2. the technical reason they cannot both hold
3. a minimal proposed resolution

Do not resolve it by guessing in code.
