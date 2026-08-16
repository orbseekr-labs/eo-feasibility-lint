"""EFL501 / EFL502 - night operation requirements.

Which sensing capability is judged depends on what the requirement explicitly
selects:

* ``spectral_bands_all_of`` present - every named family must work at night, so
  each offending family produces its own finding.
* only ``modality_any_of`` present - the required modalities' families are
  alternatives, so the most favourable outcome among them wins.
* neither present - every family the mission has is an alternative, so the most
  favourable outcome wins.

An explicitly required family is never rescued by some other family the mission
happens to carry.

Only available band families are ever evaluated, and catalog integrity validation
guarantees that every available family resolves to an explicit night-support state
(true, false or occasional). Night support is never assumed to be false because
the catalog is silent.
"""

from __future__ import annotations

from ..catalog import Mission
from ..loader import Requirement
from ..models import BAND_FAMILY_MODALITY, CONDITIONAL, FAIL, Finding

_UNAVAILABLE = (
    "EFL501",
    FAIL,
    "Night operation unavailable",
)
_CONDITIONAL = (
    "EFL502",
    CONDITIONAL,
    "Night operation conditional",
)


def _message(family: str, support) -> str:
    if support == "occasional":
        return (
            f"Night acquisition with the {family} band family is technically possible "
            "but is not treated as guaranteed nominal availability."
        )
    return f"The {family} band family does not support night operation."


def _finding(mission: Mission, family: str, support, required: dict) -> Finding:
    code, effect, title = _CONDITIONAL if support == "occasional" else _UNAVAILABLE
    return Finding(
        code=code,
        effect=effect,
        title=title,
        message=_message(family, support),
        required=required,
        capability={"band_family": family, "night_support": support},
        source_ids=mission.sources_for("night_support"),
    )


def evaluate(requirement: Requirement, mission: Mission) -> list[Finding]:
    if requirement.must_support_night is not True:
        return []

    if requirement.spectral_bands_all_of:
        findings = []
        for family in requirement.spectral_bands_all_of:
            if not mission.band_available(family):
                # Reported by the spectral rule.
                continue
            support = mission.night_support_for(family)
            if support is True:
                continue
            findings.append(
                _finding(
                    mission,
                    family,
                    support,
                    {
                        "must_support_night": True,
                        "band_family": family,
                        "selection": "all_of",
                    },
                )
            )
        return findings

    candidates = [
        family
        for family in mission.available_families()
        if not requirement.modality_any_of
        or BAND_FAMILY_MODALITY[family] in requirement.modality_any_of
    ]
    if not candidates:
        # No candidate capability exists at all; the modality rule reports that.
        return []

    supports = {family: mission.night_support_for(family) for family in candidates}
    if any(support is True for support in supports.values()):
        return []

    best_family = next(
        (family for family in candidates if supports[family] == "occasional"),
        candidates[0],
    )
    return [
        _finding(
            mission,
            best_family,
            supports[best_family],
            {
                "must_support_night": True,
                "band_families": list(candidates),
                "selection": "any_of",
            },
        )
    ]
