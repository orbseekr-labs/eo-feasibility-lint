"""EFL202 - required spectral band family availability."""

from __future__ import annotations

from ..catalog import Mission
from ..loader import Requirement
from ..models import BAND_FAMILIES, FAIL, Finding


def evaluate(requirement: Requirement, mission: Mission) -> list[Finding]:
    findings: list[Finding] = []
    required = set(requirement.spectral_bands_all_of)
    for family in BAND_FAMILIES:
        if family not in required or mission.band_available(family):
            continue
        findings.append(
            Finding(
                code="EFL202",
                effect=FAIL,
                title="Required spectral band family unavailable",
                message=(
                    f"The mission does not provide the {family} band family."
                ),
                required={"spectral_band_family": family},
                capability={"band_family": family, "available": False},
                # An absence conclusion cites the source designated as
                # authoritative for the mission's complete band inventory.
                source_ids=mission.band_inventory_source_ids,
            )
        )
    return findings
