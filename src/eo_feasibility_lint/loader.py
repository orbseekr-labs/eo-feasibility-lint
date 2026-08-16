"""Requirement document loading and strict schema validation.

Validation is hand-written on purpose: the runtime dependency surface is limited
to PyYAML, so no JSON Schema library is available. ``schemas/requirement.schema.json``
documents the same contract and is kept in sync by ``tests/test_schema.py``.

YAML is parsed with a SafeLoader subclass only. No arbitrary object construction,
no template evaluation, no code execution from requirement documents.

Duplicate mapping keys are rejected rather than silently resolved last-value-wins,
in both YAML and JSON, so an ambiguous document can never be interpreted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from .models import BAND_FAMILIES, MODALITIES, OUTPUT_KINDS, SCHEMA_VERSION

NAME_MIN_LENGTH = 1
NAME_MAX_LENGTH = 100

TOP_LEVEL_KEYS = ("schema_version", "name", "objective", "candidate_missions", "requirements")
REQUIREMENT_KEYS = (
    "modality_any_of",
    "spectral_bands_all_of",
    "spatial",
    "temporal",
    "illumination",
    "weather",
    "coverage",
    "output",
)
SPATIAL_KEYS = ("optical_max_gsd_m", "thermal_max_gsd_m", "sar_max_resolution_m")
TEMPORAL_KEYS = ("max_nominal_revisit_days",)
ILLUMINATION_KEYS = ("must_support_night",)
WEATHER_KEYS = ("must_support_all_weather",)
COVERAGE_KEYS = ("min_single_pass_swath_km",)
OUTPUT_KEYS = ("kind",)


class RequirementError(Exception):
    """The requirement document is invalid. Reported as a usage error, never a verdict."""


class StrictSafeLoader(yaml.SafeLoader):
    """``yaml.SafeLoader`` that refuses duplicate mapping keys.

    PyYAML normally accepts a repeated key and keeps the last value, which makes
    a document's meaning depend on parser behaviour rather than on what it says.
    Such a document is ambiguous, so it is rejected instead.
    """

    def construct_mapping(self, node, deep=False):
        seen: set = set()
        for key_node, _value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in seen
            except TypeError:
                # Unhashable key; SafeLoader reports it properly below.
                continue
            if duplicate:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
            seen.add(key)
        return super().construct_mapping(node, deep)


def safe_load_yaml(text: str):
    """Parse YAML safely, rejecting duplicate mapping keys.

    ``StrictSafeLoader`` subclasses ``yaml.SafeLoader``, so this is equivalent to
    ``yaml.safe_load`` plus the duplicate-key check.
    """
    return yaml.load(text, Loader=StrictSafeLoader)


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict:
    seen: set[str] = set()
    for key, _value in pairs:
        if key in seen:
            raise ValueError(f"found duplicate key {key!r}")
        seen.add(key)
    return dict(pairs)


def safe_load_json(text: str):
    """Parse JSON, rejecting duplicate object keys."""
    return json.loads(text, object_pairs_hook=_reject_duplicate_json_keys)


@dataclass(frozen=True)
class Requirement:
    name: str
    output_kind: str
    objective: str | None = None
    candidate_missions: tuple[str, ...] | None = None
    modality_any_of: tuple[str, ...] = ()
    spectral_bands_all_of: tuple[str, ...] = ()
    optical_max_gsd_m: float | None = None
    thermal_max_gsd_m: float | None = None
    sar_max_resolution_m: float | None = None
    max_nominal_revisit_days: float | None = None
    must_support_night: bool | None = None
    must_support_all_weather: bool | None = None
    min_single_pass_swath_km: float | None = None

    def has_testable_requirements(self) -> bool:
        """True when at least one constraint the v0.1 rules can evaluate is present.

        ``must_support_night: false`` and ``must_support_all_weather: false`` are
        not constraints: they can never contradict a mission capability.
        """
        return any(
            [
                bool(self.modality_any_of),
                bool(self.spectral_bands_all_of),
                self.optical_max_gsd_m is not None,
                self.thermal_max_gsd_m is not None,
                self.sar_max_resolution_m is not None,
                self.max_nominal_revisit_days is not None,
                self.must_support_night is True,
                self.must_support_all_weather is True,
                self.min_single_pass_swath_km is not None,
            ]
        )


def _require_mapping(value, where: str) -> dict:
    if not isinstance(value, dict):
        raise RequirementError(f"{where}: expected a mapping, got {type(value).__name__}")
    return value


def _reject_unknown_keys(mapping: dict, allowed: tuple[str, ...], where: str) -> None:
    unknown = sorted(set(mapping) - set(allowed))
    if unknown:
        raise RequirementError(
            f"{where}: unknown key(s) {', '.join(unknown)}; allowed: {', '.join(allowed)}"
        )


def _positive_number(value, where: str) -> float | int:
    """Validate a positive number, preserving int-ness so reports stay clean."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RequirementError(f"{where}: expected a positive number, got {value!r}")
    if value <= 0:
        raise RequirementError(f"{where}: expected a positive number, got {value!r}")
    return value


def _boolean(value, where: str) -> bool:
    if not isinstance(value, bool):
        raise RequirementError(f"{where}: expected true or false, got {value!r}")
    return value


def _string_list(value, allowed: tuple[str, ...], where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise RequirementError(f"{where}: expected a non-empty list")
    items: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise RequirementError(f"{where}[{index}]: expected a string, got {item!r}")
        if item not in allowed:
            raise RequirementError(
                f"{where}[{index}]: unknown value {item!r}; allowed: {', '.join(allowed)}"
            )
        items.append(item)
    duplicates = sorted({item for item in items if items.count(item) > 1})
    if duplicates:
        raise RequirementError(f"{where}: duplicate value(s) {', '.join(duplicates)}")
    return tuple(items)


def parse_requirement(document, supported_mission_ids: tuple[str, ...]) -> Requirement:
    """Validate a already-deserialised requirement document."""
    document = _require_mapping(document, "document")
    _reject_unknown_keys(document, TOP_LEVEL_KEYS, "document")

    if "schema_version" not in document:
        raise RequirementError("document: schema_version is required")
    schema_version = document["schema_version"]
    if schema_version != SCHEMA_VERSION:
        raise RequirementError(
            f"document.schema_version: only {SCHEMA_VERSION!r} is accepted, got "
            f"{schema_version!r}"
        )

    name = document.get("name")
    if not isinstance(name, str):
        raise RequirementError("document.name: is required and must be a string")
    if not NAME_MIN_LENGTH <= len(name) <= NAME_MAX_LENGTH:
        raise RequirementError(
            f"document.name: must be {NAME_MIN_LENGTH}-{NAME_MAX_LENGTH} characters"
        )

    objective = document.get("objective")
    if objective is not None and not isinstance(objective, str):
        raise RequirementError("document.objective: must be a string when present")

    candidate_missions: tuple[str, ...] | None = None
    if "candidate_missions" in document:
        candidate_missions = _string_list(
            document["candidate_missions"], supported_mission_ids, "document.candidate_missions"
        )

    requirements = _require_mapping(
        document.get("requirements", {}), "document.requirements"
    )
    _reject_unknown_keys(requirements, REQUIREMENT_KEYS, "document.requirements")

    modality_any_of: tuple[str, ...] = ()
    if "modality_any_of" in requirements:
        modality_any_of = _string_list(
            requirements["modality_any_of"], MODALITIES, "requirements.modality_any_of"
        )

    spectral_bands_all_of: tuple[str, ...] = ()
    if "spectral_bands_all_of" in requirements:
        spectral_bands_all_of = _string_list(
            requirements["spectral_bands_all_of"],
            BAND_FAMILIES,
            "requirements.spectral_bands_all_of",
        )

    spatial = _require_mapping(requirements.get("spatial", {}), "requirements.spatial")
    _reject_unknown_keys(spatial, SPATIAL_KEYS, "requirements.spatial")
    spatial_values = {
        key: _positive_number(spatial[key], f"requirements.spatial.{key}")
        for key in SPATIAL_KEYS
        if key in spatial
    }

    temporal = _require_mapping(requirements.get("temporal", {}), "requirements.temporal")
    _reject_unknown_keys(temporal, TEMPORAL_KEYS, "requirements.temporal")
    max_nominal_revisit_days = None
    if "max_nominal_revisit_days" in temporal:
        max_nominal_revisit_days = _positive_number(
            temporal["max_nominal_revisit_days"],
            "requirements.temporal.max_nominal_revisit_days",
        )

    illumination = _require_mapping(
        requirements.get("illumination", {}), "requirements.illumination"
    )
    _reject_unknown_keys(illumination, ILLUMINATION_KEYS, "requirements.illumination")
    must_support_night = None
    if "must_support_night" in illumination:
        must_support_night = _boolean(
            illumination["must_support_night"],
            "requirements.illumination.must_support_night",
        )

    weather = _require_mapping(requirements.get("weather", {}), "requirements.weather")
    _reject_unknown_keys(weather, WEATHER_KEYS, "requirements.weather")
    must_support_all_weather = None
    if "must_support_all_weather" in weather:
        must_support_all_weather = _boolean(
            weather["must_support_all_weather"],
            "requirements.weather.must_support_all_weather",
        )

    coverage = _require_mapping(requirements.get("coverage", {}), "requirements.coverage")
    _reject_unknown_keys(coverage, COVERAGE_KEYS, "requirements.coverage")
    min_single_pass_swath_km = None
    if "min_single_pass_swath_km" in coverage:
        min_single_pass_swath_km = _positive_number(
            coverage["min_single_pass_swath_km"],
            "requirements.coverage.min_single_pass_swath_km",
        )

    if "output" not in requirements:
        raise RequirementError("requirements.output: is required")
    output = _require_mapping(requirements["output"], "requirements.output")
    _reject_unknown_keys(output, OUTPUT_KEYS, "requirements.output")
    output_kind = output.get("kind")
    if output_kind not in OUTPUT_KINDS:
        raise RequirementError(
            f"requirements.output.kind: must be one of {', '.join(OUTPUT_KINDS)}; "
            f"got {output_kind!r}"
        )

    return Requirement(
        name=name,
        output_kind=output_kind,
        objective=objective,
        candidate_missions=candidate_missions,
        modality_any_of=modality_any_of,
        spectral_bands_all_of=spectral_bands_all_of,
        optical_max_gsd_m=spatial_values.get("optical_max_gsd_m"),
        thermal_max_gsd_m=spatial_values.get("thermal_max_gsd_m"),
        sar_max_resolution_m=spatial_values.get("sar_max_resolution_m"),
        max_nominal_revisit_days=max_nominal_revisit_days,
        must_support_night=must_support_night,
        must_support_all_weather=must_support_all_weather,
        min_single_pass_swath_km=min_single_pass_swath_km,
    )


def load_requirement(path: str | Path, supported_mission_ids: tuple[str, ...]) -> Requirement:
    """Read and validate a requirement file (``.yaml``, ``.yml`` or ``.json``)."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in (".yaml", ".yml", ".json"):
        raise RequirementError(
            f"{path}: unsupported file type {suffix or '(none)'}; expected .yaml, .yml or .json"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise RequirementError(f"{path}: cannot be read ({error.strerror})") from error

    try:
        document = safe_load_json(text) if suffix == ".json" else safe_load_yaml(text)
    except (yaml.YAMLError, ValueError) as error:
        raise RequirementError(f"{path}: cannot be parsed ({error})") from error

    if document is None:
        raise RequirementError(f"{path}: document is empty")

    return parse_requirement(document, supported_mission_ids)
