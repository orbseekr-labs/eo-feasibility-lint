"""Text and JSON rendering.

JSON output never contains a timestamp, hostname, username, filesystem path or
random id. The same input plus the same catalog and ruleset versions always
renders byte-for-byte identical output.
"""

from __future__ import annotations

import json
import textwrap

from .catalog import Catalog, Mission
from .models import BAND_FAMILIES, REASON_CODES, RULESET_VERSION, Finding, Report

WRAP_WIDTH = 79

REVISIT_SCOPE_TEXT = {
    "equator_constellation_nominal": "at equator, nominal constellation",
    "equator_two_satellite_nominal": "at equator, nominal two-satellite constellation",
    "nominal_repeat_cycle": "nominal repeat cycle",
    "nominal_combined_offset": "nominal combined Landsat 8 + 9 offset",
}

NIGHT_SUPPORT_TEXT = {True: "yes", False: "no", "occasional": "occasional"}

#: Printed under every report. PASS must never be read as a project guarantee.
SCOPE_NOTICE = (
    "PASS is not a guarantee that a real EO project will succeed. Only the "
    "explicit requirements above were checked, against a static mission catalog. "
    "Acquisition, cloud cover, image quality, model accuracy, detection accuracy, "
    "tasking availability and revisit at a specific location were not evaluated."
)


def _number(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _days(value) -> str:
    return f"{_number(value)} day" if value == 1 else f"{_number(value)} days"


def _wrap(text: str) -> list[str]:
    return textwrap.wrap(text, width=WRAP_WIDTH) or [""]


# --- Per-code human phrasing of the required / capability payloads ---------


def _required_text(finding: Finding) -> str | None:
    required = finding.required
    code = finding.code

    if code == "EFL201":
        if "modality_any_of" in required:
            return "any of: " + ", ".join(required["modality_any_of"])
        return f"{required['modality']} (implied by {required['implied_by']})"
    if code == "EFL202":
        return f"band family: {required['spectral_band_family']}"
    if code == "EFL301":
        limit = f"<= {_number(required['optical_max_gsd_m'])} m optical GSD"
        family = required.get("band_family")
        return f"{limit} ({family})" if family else limit
    if code == "EFL302":
        return f"<= {_number(required['thermal_max_gsd_m'])} m thermal GSD"
    if code == "EFL303":
        return f"<= {_number(required['sar_max_resolution_m'])} m SAR resolution"
    if code in ("EFL401", "EFL402"):
        return f"<= {_days(required['max_nominal_revisit_days'])}"
    if code in ("EFL501", "EFL502"):
        if required.get("selection") == "all_of":
            return f"night operation ({required['band_family']})"
        return "night operation (" + ", ".join(required["band_families"]) + ")"
    if code == "EFL601":
        return "all-weather operation"
    if code == "EFL701":
        return f">= {_number(required['min_single_pass_swath_km'])} km single-pass swath"
    if code in ("EFL801", "EFL802", "EFL803"):
        return f"output kind: {required['output_kind']}"
    return None


def _capability_text(finding: Finding) -> str | None:
    capability = finding.capability
    code = finding.code

    if code == "EFL201":
        modalities = capability.get("modalities") or []
        available = ", ".join(modalities) if modalities else "none"
        return f"mission modalities: {available}"
    if code == "EFL202":
        return f"{capability['band_family']} not available"
    if code in ("EFL301", "EFL302"):
        resolution = _number(capability["resolution_m"])
        if capability.get("basis") == "default_multispectral_gsd_m":
            return f"default multispectral GSD = {resolution} m (panchromatic excluded)"
        return f"{capability['band_family']} = {resolution} m"
    if code == "EFL303":
        return (
            f"{_number(capability['range_m'])} m range x "
            f"{_number(capability['azimuth_m'])} m azimuth; compared at "
            f"{_number(capability['compared_resolution_m'])} m"
        )
    if code in ("EFL401", "EFL402"):
        scope = REVISIT_SCOPE_TEXT.get(capability["scope"], capability["scope"])
        return f"{_days(capability['nominal_revisit_days'])} {scope}"
    if code in ("EFL501", "EFL502"):
        support = NIGHT_SUPPORT_TEXT.get(
            capability["night_support"], str(capability["night_support"])
        )
        return f"{capability['band_family']} night support: {support}"
    if code == "EFL601":
        return "not all-weather; depends on cloud-free conditions"
    if code == "EFL701":
        return f"{_number(capability['swath_km'])} km"
    return None


# --- Report rendering -----------------------------------------------------


def _render_finding(finding: Finding) -> list[str]:
    lines = [f"{finding.code} {finding.effect}", f"{finding.title}."]
    lines += _wrap(finding.message)

    required = _required_text(finding)
    if required is not None:
        lines += ["", "Required:", required]

    capability = _capability_text(finding)
    if capability is not None:
        lines += ["", "Catalog:", capability]

    if finding.source_ids:
        lines += ["", "Sources:", ", ".join(finding.source_ids)]

    return lines


def render_text(report: Report) -> str:
    lines = [
        "EO FEASIBILITY LINT",
        "",
        "Requirement:",
        report.requirement_name,
        "",
        "Ruleset:",
        RULESET_VERSION,
        "",
        "Catalog:",
        report.catalog_version,
    ]

    for result in report.mission_results:
        lines += ["", result.mission_id, "-" * (len(result.mission_id) + 2), ""]
        lines.append(f"Verdict: {result.verdict}")
        if not result.findings:
            lines += ["", "No findings."]
        for finding in result.findings:
            lines.append("")
            lines += _render_finding(finding)

    lines += ["", "Portfolio verdict:", report.portfolio_verdict, ""]
    lines += _wrap(SCOPE_NOTICE)
    return "\n".join(lines) + "\n"


def render_json(report: Report) -> str:
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n"


# --- Catalog and rule introspection ---------------------------------------


def render_mission_list(catalog: Catalog) -> str:
    lines = [f"Catalog: {catalog.version}", ""]
    width = max(len(mission.id) for mission in catalog.missions)
    for mission in catalog.missions:
        lines.append(f"{mission.id.ljust(width)}  {mission.display_name}")
    return "\n".join(lines) + "\n"


def render_mission(catalog: Catalog, mission: Mission) -> str:
    lines = [
        mission.display_name,
        "-" * len(mission.display_name),
        "",
        f"id: {mission.id}",
        f"catalog: {catalog.version}",
        f"modalities: {', '.join(mission.modalities)}",
        (
            f"nominal revisit: {_days(mission.revisit_days)} "
            f"({REVISIT_SCOPE_TEXT.get(mission.revisit_scope, mission.revisit_scope)})"
        ),
        f"single-pass swath: {_number(mission.swath_km)} km",
        f"all-weather: {'yes' if mission.all_weather else 'no'}",
    ]

    if mission.default_multispectral_gsd_m is not None:
        lines.append(
            "default multispectral GSD: "
            f"{_number(mission.default_multispectral_gsd_m)} m "
            "(used when no optical band family is named; panchromatic excluded)"
        )

    lines += ["", "Band families:"]

    for family in BAND_FAMILIES:
        if not mission.band_available(family):
            lines.append(f"  {family}: not available")
            continue
        if family == "c_band_sar":
            resolution = mission.bands[family].get("resolution") or {}
            detail = (
                f"{_number(resolution.get('range_m'))} m range x "
                f"{_number(resolution.get('azimuth_m'))} m azimuth"
            )
        else:
            detail = f"{_number(mission.band_resolution_m(family))} m"
        night = NIGHT_SUPPORT_TEXT.get(
            mission.night_support_for(family), str(mission.night_support_for(family))
        )
        lines.append(f"  {family}: {detail} (night: {night})")

    lines += ["", "Sources:"]
    for source_id in mission.source_ids:
        source = catalog.source(source_id)
        if source is None:
            continue
        lines.append(f"  {source.id}")
        lines.append(f"    {source.title} - {source.publisher}")
        lines.append(f"    {source.url}")

    lines += [
        "",
        "These sources are provenance only. The runtime never fetches them.",
    ]
    return "\n".join(lines) + "\n"


def render_rules() -> str:
    lines = [f"Ruleset: {RULESET_VERSION}", ""]
    category = None
    for reason in REASON_CODES:
        if reason.category != category:
            category = reason.category
            lines += [category, "-" * len(category)]
        lines.append(f"{reason.code} {reason.name} -> {reason.effect}")
        lines += [f"  {line}" for line in textwrap.wrap(reason.summary, width=WRAP_WIDTH - 2)]
        lines.append("")
    return "\n".join(lines)
