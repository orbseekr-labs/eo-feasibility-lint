"""EFL301 / EFL302 / EFL303 - spatial resolution requirements, plus EFL201.

Optical GSD, thermal GSD and SAR resolution are separate requirement fields and
are never compared against each other. SAR resolution is not physically
identical to optical GSD.

A sensor-family-specific spatial requirement implies that the corresponding
modality is required. When the mission does not have that modality at all the
finding is EFL201 (modality unavailable), not EFL30x: EFL30x means the modality
exists but its resolution does not meet the numeric requirement.
"""

from __future__ import annotations

from ..catalog import Mission
from ..loader import Requirement
from ..models import BAND_FAMILY_MODALITY, FAIL, Finding

#: requirement field -> (implied modality, unmet reason code)
FIELD_MODALITY = {
    "optical_max_gsd_m": ("optical_multispectral", "EFL301"),
    "thermal_max_gsd_m": ("thermal_ir", "EFL302"),
    "sar_max_resolution_m": ("sar_c_band", "EFL303"),
}

TITLES = {
    "EFL301": "Optical GSD requirement unmet",
    "EFL302": "Thermal GSD requirement unmet",
    "EFL303": "SAR resolution requirement unmet",
}


def _modality_unavailable(mission: Mission, field: str, modality: str) -> Finding:
    return Finding(
        code="EFL201",
        effect=FAIL,
        title="Required modality unavailable",
        message=(
            f"The mission does not provide the {modality} modality implied by the "
            f"spatial.{field} requirement."
        ),
        required={"modality": modality, "implied_by": f"spatial.{field}"},
        capability={"modalities": list(mission.modalities)},
        source_ids=mission.modality_inventory_source_ids,
    )


def _optical(requirement: Requirement, mission: Mission) -> list[Finding]:
    limit = requirement.optical_max_gsd_m
    findings: list[Finding] = []

    explicit = [
        family
        for family in requirement.spectral_bands_all_of
        if BAND_FAMILY_MODALITY[family] == "optical_multispectral"
    ]

    if explicit:
        for family in explicit:
            resolution = mission.band_resolution_m(family)
            if resolution is None or resolution <= limit:
                # Unavailable families are reported by the spectral rule.
                continue
            findings.append(
                Finding(
                    code="EFL301",
                    effect=FAIL,
                    title=TITLES["EFL301"],
                    message=(
                        f"The mission's {family} ground sample distance is coarser than "
                        "the requirement."
                    ),
                    required={"optical_max_gsd_m": limit, "band_family": family},
                    capability={"band_family": family, "resolution_m": resolution},
                    source_ids=mission.sources_for(f"bands.{family}"),
                )
            )
        return findings

    # No optical family was named, so the mission's explicitly catalogued default
    # multispectral GSD applies. It is catalog data, never inferred from the band
    # table, and panchromatic never stands in for it.
    resolution = mission.default_multispectral_gsd_m
    if resolution is None or resolution <= limit:
        return findings
    return [
        Finding(
            code="EFL301",
            effect=FAIL,
            title=TITLES["EFL301"],
            message=(
                "The mission's default multispectral ground sample distance is coarser "
                "than the requirement. Panchromatic resolution is never substituted for "
                "the multispectral capability."
            ),
            required={"optical_max_gsd_m": limit},
            capability={
                "basis": "default_multispectral_gsd_m",
                "resolution_m": resolution,
            },
            source_ids=mission.sources_for("default_multispectral_gsd_m"),
        )
    ]


def _thermal(requirement: Requirement, mission: Mission) -> list[Finding]:
    limit = requirement.thermal_max_gsd_m
    resolution = mission.band_resolution_m("thermal_ir")
    if resolution is None or resolution <= limit:
        return []
    return [
        Finding(
            code="EFL302",
            effect=FAIL,
            title=TITLES["EFL302"],
            message=(
                "The mission's thermal infrared ground sample distance is coarser than "
                "the requirement."
            ),
            required={"thermal_max_gsd_m": limit},
            capability={"band_family": "thermal_ir", "resolution_m": resolution},
            source_ids=mission.sources_for("bands.thermal_ir"),
        )
    ]


def _sar(requirement: Requirement, mission: Mission) -> list[Finding]:
    limit = requirement.sar_max_resolution_m
    band = mission.bands.get("c_band_sar", {})
    resolution = mission.sar_nominal_resolution_m()
    if resolution is None or resolution <= limit:
        return []
    dimensions = band.get("resolution") or {}
    return [
        Finding(
            code="EFL303",
            effect=FAIL,
            title=TITLES["EFL303"],
            message=(
                "The mission's nominal SAR resolution is coarser than the requirement. "
                "The larger (worse) nominal dimension is used, which is intentionally "
                "conservative."
            ),
            required={"sar_max_resolution_m": limit},
            capability={
                "band_family": "c_band_sar",
                "range_m": dimensions.get("range_m"),
                "azimuth_m": dimensions.get("azimuth_m"),
                "compared_resolution_m": resolution,
            },
            source_ids=mission.sources_for("bands.c_band_sar"),
        )
    ]


_EVALUATORS = {
    "optical_max_gsd_m": _optical,
    "thermal_max_gsd_m": _thermal,
    "sar_max_resolution_m": _sar,
}


def evaluate(requirement: Requirement, mission: Mission) -> list[Finding]:
    findings: list[Finding] = []
    for field, (modality, _code) in FIELD_MODALITY.items():
        if getattr(requirement, field) is None:
            continue
        if not mission.has_modality(modality):
            findings.append(_modality_unavailable(mission, field, modality))
            continue
        findings.extend(_EVALUATORS[field](requirement, mission))
    return findings
