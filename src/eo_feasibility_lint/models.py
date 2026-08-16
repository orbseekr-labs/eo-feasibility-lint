"""Core vocabulary, verdicts, findings and the public reason-code registry.

Everything in this module is part of the v0.1 public contract. Reason codes are
public API: once released, a code MUST NEVER be reused for a different meaning.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

SCHEMA_VERSION = "0.1"
RULESET_VERSION = "0.1.0"

# --- Verdicts -------------------------------------------------------------

PASS = "PASS"
CONDITIONAL = "CONDITIONAL"
UNKNOWN = "UNKNOWN"
FAIL = "FAIL"

VERDICTS = (PASS, CONDITIONAL, UNKNOWN, FAIL)

#: Severity threshold scale (spec section 40).
SEVERITY = {PASS: 0, CONDITIONAL: 1, UNKNOWN: 2, FAIL: 3}


def worst(verdicts: list[str]) -> str:
    """Per-mission precedence: FAIL > UNKNOWN > CONDITIONAL > PASS."""
    return max(verdicts, key=lambda v: SEVERITY[v], default=PASS)


def best(verdicts: list[str]) -> str:
    """Portfolio precedence: PASS > CONDITIONAL > UNKNOWN > FAIL."""
    return min(verdicts, key=lambda v: SEVERITY[v], default=UNKNOWN)


# --- Sensing vocabulary ---------------------------------------------------

MODALITIES = ("optical_multispectral", "thermal_ir", "sar_c_band")

BAND_FAMILIES = (
    "visible",
    "coastal_aerosol",
    "nir",
    "red_edge",
    "swir",
    "water_vapor",
    "cirrus",
    "panchromatic",
    "thermal_ir",
    "c_band_sar",
)

#: Which modality each band family belongs to.
BAND_FAMILY_MODALITY = {
    "visible": "optical_multispectral",
    "coastal_aerosol": "optical_multispectral",
    "nir": "optical_multispectral",
    "red_edge": "optical_multispectral",
    "swir": "optical_multispectral",
    "water_vapor": "optical_multispectral",
    "cirrus": "optical_multispectral",
    "panchromatic": "optical_multispectral",
    "thermal_ir": "thermal_ir",
    "c_band_sar": "sar_c_band",
}

#: Night-support group key used when a mission does not state a per-family value.
BAND_FAMILY_NIGHT_GROUP = {
    "visible": "reflected_optical",
    "coastal_aerosol": "reflected_optical",
    "nir": "reflected_optical",
    "red_edge": "reflected_optical",
    "swir": "reflected_optical",
    "water_vapor": "reflected_optical",
    "cirrus": "reflected_optical",
    "panchromatic": "reflected_optical",
    "thermal_ir": "thermal_ir",
    "c_band_sar": "c_band_sar",
}

OUTPUT_KINDS = (
    "instrument_measurement",
    "derived_product",
    "model_inference",
    "business_metric",
)

REVISIT_SCOPES = (
    "equator_constellation_nominal",
    "equator_two_satellite_nominal",
    "nominal_repeat_cycle",
    "nominal_combined_offset",
)

NIGHT_SUPPORT_VALUES = (True, False, "occasional")


# --- Reason codes ---------------------------------------------------------


@dataclass(frozen=True)
class ReasonCode:
    """A public reason-code identifier.

    A code identifies a finding TYPE, not a unique finding instance: the same
    code may appear several times in one mission result when several independent
    requirements produce the same type of finding. Each such finding carries
    enough ``required``/``capability`` detail to tell them apart.

    Every code in this registry is reachable. v0.1 does not reserve unused codes.
    """

    code: str
    name: str
    category: str
    effect: str
    summary: str


REASON_CODES: tuple[ReasonCode, ...] = (
    ReasonCode(
        "EFL201",
        "REQUIRED_MODALITY_UNAVAILABLE",
        "Modality / Spectral",
        FAIL,
        "A required sensing modality is not available on the mission.",
    ),
    ReasonCode(
        "EFL202",
        "REQUIRED_BAND_UNAVAILABLE",
        "Modality / Spectral",
        FAIL,
        "A required spectral band family is not available on the mission.",
    ),
    ReasonCode(
        "EFL301",
        "OPTICAL_GSD_REQUIREMENT_UNMET",
        "Spatial",
        FAIL,
        "The mission's optical ground sample distance is coarser than required.",
    ),
    ReasonCode(
        "EFL302",
        "THERMAL_GSD_REQUIREMENT_UNMET",
        "Spatial",
        FAIL,
        "The mission's thermal ground sample distance is coarser than required.",
    ),
    ReasonCode(
        "EFL303",
        "SAR_RESOLUTION_REQUIREMENT_UNMET",
        "Spatial",
        FAIL,
        "The mission's nominal SAR resolution is coarser than required.",
    ),
    ReasonCode(
        "EFL401",
        "NOMINAL_REVISIT_TOO_SLOW",
        "Temporal",
        FAIL,
        "The mission's nominal revisit interval is longer than required.",
    ),
    ReasonCode(
        "EFL402",
        "NOMINAL_REVISIT_NOT_AVAILABILITY_GUARANTEE",
        "Temporal",
        PASS,
        "Informational: nominal revisit is not a guarantee of usable observation "
        "frequency. Never changes a verdict.",
    ),
    ReasonCode(
        "EFL501",
        "NIGHT_OPERATION_UNAVAILABLE",
        "Illumination",
        FAIL,
        "Night operation is not available for the required sensing capability.",
    ),
    ReasonCode(
        "EFL502",
        "NIGHT_OPERATION_CONDITIONAL",
        "Illumination",
        CONDITIONAL,
        "Night operation is technically possible but not treated as guaranteed "
        "nominal availability.",
    ),
    ReasonCode(
        "EFL601",
        "ALL_WEATHER_REQUIREMENT_UNMET",
        "Weather",
        FAIL,
        "The mission depends on cloud-free conditions in the way optical and "
        "thermal imaging does.",
    ),
    ReasonCode(
        "EFL701",
        "SINGLE_PASS_SWATH_REQUIREMENT_UNMET",
        "Coverage",
        FAIL,
        "The mission's single-pass swath is narrower than required.",
    ),
    ReasonCode(
        "EFL801",
        "DERIVED_PROCESSING_REQUIRED",
        "Output / Inference",
        CONDITIONAL,
        "The requested output requires processing beyond raw acquisition.",
    ),
    ReasonCode(
        "EFL802",
        "MODEL_VALIDATION_REQUIRED",
        "Output / Inference",
        CONDITIONAL,
        "The requested output requires a model that mission specifications alone "
        "cannot validate.",
    ),
    ReasonCode(
        "EFL803",
        "BUSINESS_METRIC_INFERENCE_REQUIRED",
        "Output / Inference",
        CONDITIONAL,
        "The requested output is not directly observable from mission "
        "specifications and requires an external inference chain.",
    ),
    ReasonCode(
        "EFL901",
        "NO_TESTABLE_REQUIREMENTS",
        "Knowledge Limit",
        UNKNOWN,
        "No technical requirement that v0.1 knows how to evaluate was supplied.",
    ),
)

REASON_CODES_BY_CODE = {rc.code: rc for rc in REASON_CODES}


# --- Findings and results -------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """A single deterministic rule outcome.

    ``source_ids`` must be non-empty whenever the finding depends on a mission
    capability (spec section 30).
    """

    code: str
    effect: str
    title: str
    message: str
    required: dict = field(default_factory=dict)
    capability: dict = field(default_factory=dict)
    source_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "effect": self.effect,
            "title": self.title,
            "message": self.message,
            "required": self.required,
            "capability": self.capability,
            "source_ids": list(self.source_ids),
        }

    def sort_key(self) -> tuple[str, str, str]:
        """Ascending reason code, then a stable payload tiebreaker."""
        return (
            self.code,
            json.dumps(self.required, sort_keys=True),
            json.dumps(self.capability, sort_keys=True),
        )


@dataclass(frozen=True)
class MissionResult:
    mission_id: str
    verdict: str
    findings: tuple[Finding, ...]

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "verdict": self.verdict,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass(frozen=True)
class Report:
    requirement_name: str
    catalog_version: str
    portfolio_verdict: str
    mission_results: tuple[MissionResult, ...]

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "ruleset_version": RULESET_VERSION,
            "catalog_version": self.catalog_version,
            "requirement": {"name": self.requirement_name},
            "portfolio_verdict": self.portfolio_verdict,
            "mission_results": [m.to_dict() for m in self.mission_results],
        }
