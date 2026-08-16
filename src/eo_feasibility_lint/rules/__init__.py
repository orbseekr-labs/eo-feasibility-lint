"""Deterministic rule units.

Each module exposes ``evaluate(requirement, mission) -> list[Finding]`` and is
independently testable. A rule never reads anything outside the requirement
document and the static catalog.
"""

from . import (
    coverage,
    illumination,
    modality,
    output_kind,
    spatial,
    spectral,
    temporal,
    weather,
)

#: Capability rules, in fixed execution order. Output-kind is applied separately
#: because it is evaluated even when no testable technical requirement exists.
CAPABILITY_RULES = (
    modality,
    spectral,
    spatial,
    temporal,
    illumination,
    weather,
    coverage,
)

__all__ = [
    "CAPABILITY_RULES",
    "coverage",
    "illumination",
    "modality",
    "output_kind",
    "spatial",
    "spectral",
    "temporal",
    "weather",
]
