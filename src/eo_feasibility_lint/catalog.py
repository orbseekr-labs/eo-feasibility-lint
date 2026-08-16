"""Static mission catalog loading, integrity validation and capability access.

The catalog is read once from packaged YAML. Nothing here touches the network.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from typing import Any

from .loader import safe_load_yaml
from .models import (
    BAND_FAMILIES,
    BAND_FAMILY_NIGHT_GROUP,
    MODALITIES,
    NIGHT_SUPPORT_VALUES,
    REASON_CODES,
    REVISIT_SCOPES,
)

#: Mission profiles supported by v0.1 (spec section 6).
SUPPORTED_MISSION_IDS = (
    "sentinel-1-iw",
    "sentinel-2",
    "landsat-8",
    "landsat-9",
    "landsat-8-9",
)

#: Night-support group keys a mission may state instead of a per-family value.
NIGHT_GROUP_KEYS = ("reflected_optical", "thermal_ir", "c_band_sar")

#: Capability keys that rules consume and therefore must carry provenance.
SCALAR_CAPABILITY_KEYS = (
    "modalities",
    "nominal_revisit",
    "swath_km",
    "all_weather",
    "night_support",
)

#: Provenance key required only of missions with an optical multispectral payload.
OPTICAL_CAPABILITY_KEY = "default_multispectral_gsd_m"


class CatalogError(Exception):
    """The packaged catalog is internally inconsistent. This is a tool bug."""


@dataclass(frozen=True)
class Source:
    id: str
    publisher: str
    title: str
    url: str


@dataclass(frozen=True)
class Mission:
    id: str
    display_name: str
    modalities: tuple[str, ...]
    revisit_days: float
    revisit_scope: str
    swath_km: float
    default_multispectral_gsd_m: float | None
    all_weather: bool
    night_support: dict[str, Any]
    bands: dict[str, dict]
    source_ids: tuple[str, ...]
    modality_inventory_source_ids: tuple[str, ...]
    band_inventory_source_ids: tuple[str, ...]
    capability_sources: dict[str, tuple[str, ...]]

    # -- capability access -------------------------------------------------

    def has_modality(self, modality: str) -> bool:
        return modality in self.modalities

    def band_available(self, family: str) -> bool:
        return bool(self.bands.get(family, {}).get("available", False))

    def available_families(self) -> tuple[str, ...]:
        """Available band families, in canonical vocabulary order."""
        return tuple(f for f in BAND_FAMILIES if self.band_available(f))

    def band_resolution_m(self, family: str) -> float | None:
        """Nominal resolution of a non-SAR band family, in metres."""
        band = self.bands.get(family)
        if not band or not band.get("available"):
            return None
        return band.get("resolution_m")

    def sar_nominal_resolution_m(self) -> float | None:
        """Conservative SAR resolution: the larger (worse) nominal dimension.

        SAR resolution is not physically identical to optical GSD and is never
        compared against an optical requirement.
        """
        band = self.bands.get("c_band_sar")
        if not band or not band.get("available"):
            return None
        resolution = band.get("resolution") or {}
        dimensions = [
            resolution[key] for key in ("range_m", "azimuth_m") if resolution.get(key) is not None
        ]
        return max(dimensions) if dimensions else None

    def night_support_for(self, family: str) -> Any:
        """Night support for a band family: True, False or ``"occasional"``.

        Resolution order: exact family key, then the family's group key. There is
        no implicit default — ``None`` means the catalog does not state it, which
        catalog integrity validation rejects for every available family. Missing
        metadata is a catalog defect, not evidence of a missing capability.
        """
        if family in self.night_support:
            return self.night_support[family]
        group = BAND_FAMILY_NIGHT_GROUP.get(family)
        if group is not None and group in self.night_support:
            return self.night_support[group]
        return None

    def sources_for(self, capability_key: str) -> tuple[str, ...]:
        """Provenance for a positive capability value. Never falls back."""
        return self.capability_sources.get(capability_key, ())

    def revisit_capability(self) -> dict:
        return {"nominal_revisit_days": self.revisit_days, "scope": self.revisit_scope}


@dataclass(frozen=True)
class Catalog:
    version: str
    missions: tuple[Mission, ...]
    sources: tuple[Source, ...]

    def mission_ids(self) -> tuple[str, ...]:
        return tuple(m.id for m in self.missions)

    def get(self, mission_id: str) -> Mission | None:
        for mission in self.missions:
            if mission.id == mission_id:
                return mission
        return None

    def source(self, source_id: str) -> Source | None:
        for source in self.sources:
            if source.id == source_id:
                return source
        return None


def _read_packaged_yaml(filename: str) -> dict:
    path = resources.files("eo_feasibility_lint") / "data" / filename
    with resources.as_file(path) as concrete:
        return safe_load_yaml(concrete.read_text(encoding="utf-8"))


def _parse_sources(raw: dict) -> tuple[Source, ...]:
    entries = raw.get("sources") or []
    sources = []
    for entry in entries:
        sources.append(
            Source(
                id=entry["id"],
                publisher=entry.get("publisher", ""),
                title=entry.get("title", ""),
                url=entry.get("url", ""),
            )
        )
    return tuple(sources)


def _parse_mission(entry: dict) -> Mission:
    revisit = entry.get("nominal_revisit") or {}
    capability_sources = {
        key: tuple(value) for key, value in (entry.get("capability_sources") or {}).items()
    }
    return Mission(
        id=entry["id"],
        display_name=entry.get("display_name", entry["id"]),
        modalities=tuple(entry.get("modalities") or ()),
        revisit_days=revisit.get("days"),
        revisit_scope=revisit.get("scope", ""),
        swath_km=entry.get("swath_km"),
        default_multispectral_gsd_m=entry.get("default_multispectral_gsd_m"),
        all_weather=bool(entry.get("all_weather", False)),
        night_support=dict(entry.get("night_support") or {}),
        bands={name: dict(value) for name, value in (entry.get("bands") or {}).items()},
        source_ids=tuple(entry.get("source_ids") or ()),
        modality_inventory_source_ids=tuple(entry.get("modality_inventory_source_ids") or ()),
        band_inventory_source_ids=tuple(entry.get("band_inventory_source_ids") or ()),
        capability_sources=capability_sources,
    )


def validate_catalog(catalog: Catalog) -> None:
    """Raise :class:`CatalogError` on any integrity violation (spec section 46)."""
    errors: list[str] = []

    seen_source_ids: set[str] = set()
    for source in catalog.sources:
        if source.id in seen_source_ids:
            errors.append(f"duplicate source id: {source.id}")
        seen_source_ids.add(source.id)
        if not source.url:
            errors.append(f"source has no url: {source.id}")

    seen_codes: set[str] = set()
    for reason in REASON_CODES:
        if reason.code in seen_codes:
            errors.append(f"duplicate reason code: {reason.code}")
        seen_codes.add(reason.code)

    seen_mission_ids: set[str] = set()
    for mission in catalog.missions:
        prefix = f"mission {mission.id}"
        if mission.id in seen_mission_ids:
            errors.append(f"duplicate mission id: {mission.id}")
        seen_mission_ids.add(mission.id)

        if mission.id not in SUPPORTED_MISSION_IDS:
            errors.append(f"{prefix}: not a supported v0.1 mission id")

        if not mission.source_ids:
            errors.append(f"{prefix}: has no source_ids")
        for source_id in mission.source_ids:
            if source_id not in seen_source_ids:
                errors.append(f"{prefix}: unknown source id {source_id}")

        # Negative-capability findings cite an inventory source designated as
        # authoritative for the complete modality or band list. There is no
        # generic fallback, so these must exist.
        for label, inventory in (
            ("modality_inventory_source_ids", mission.modality_inventory_source_ids),
            ("band_inventory_source_ids", mission.band_inventory_source_ids),
        ):
            if not inventory:
                errors.append(f"{prefix}: has no {label}")
            for source_id in inventory:
                if source_id not in seen_source_ids:
                    errors.append(f"{prefix}: {label} cites unknown source {source_id}")

        for modality in mission.modalities:
            if modality not in MODALITIES:
                errors.append(f"{prefix}: unknown modality {modality}")

        if not isinstance(mission.revisit_days, (int, float)) or mission.revisit_days <= 0:
            errors.append(f"{prefix}: invalid nominal revisit value {mission.revisit_days!r}")
        if mission.revisit_scope not in REVISIT_SCOPES:
            errors.append(f"{prefix}: unknown revisit scope {mission.revisit_scope!r}")

        if not isinstance(mission.swath_km, (int, float)) or mission.swath_km <= 0:
            errors.append(f"{prefix}: invalid swath_km {mission.swath_km!r}")

        optical = "optical_multispectral" in mission.modalities
        default_gsd = mission.default_multispectral_gsd_m
        if optical:
            if not isinstance(default_gsd, (int, float)) or isinstance(default_gsd, bool):
                errors.append(
                    f"{prefix}: optical mission has no default_multispectral_gsd_m"
                )
            elif default_gsd <= 0:
                errors.append(f"{prefix}: invalid default_multispectral_gsd_m {default_gsd!r}")
        elif default_gsd is not None:
            errors.append(
                f"{prefix}: default_multispectral_gsd_m set on a non-optical mission"
            )

        for key, value in mission.night_support.items():
            if key not in BAND_FAMILIES and key not in NIGHT_GROUP_KEYS:
                errors.append(f"{prefix}: unknown night_support key {key}")
            if value not in NIGHT_SUPPORT_VALUES:
                errors.append(f"{prefix}: invalid night_support value {value!r} for {key}")

        # Every family that can participate in an illumination check must resolve
        # to an explicit state. Missing metadata is a catalog defect, never false.
        for family in mission.available_families():
            if mission.night_support_for(family) is None:
                errors.append(f"{prefix}: night support for {family} is not stated")

        for family, band in mission.bands.items():
            if family not in BAND_FAMILIES:
                errors.append(f"{prefix}: unknown band family {family}")
                continue
            if not band.get("available"):
                continue
            if family == "c_band_sar":
                resolution = band.get("resolution") or {}
                for key in ("range_m", "azimuth_m"):
                    value = resolution.get(key)
                    if not isinstance(value, (int, float)) or value <= 0:
                        errors.append(f"{prefix}: invalid c_band_sar {key} {value!r}")
            else:
                value = band.get("resolution_m")
                if not isinstance(value, (int, float)) or value <= 0:
                    errors.append(f"{prefix}: invalid resolution_m {value!r} for {family}")

        required_capability_keys = list(SCALAR_CAPABILITY_KEYS)
        if optical:
            required_capability_keys.append(OPTICAL_CAPABILITY_KEY)
        required_capability_keys += [f"bands.{family}" for family in mission.bands]
        for key in required_capability_keys:
            source_ids = mission.capability_sources.get(key)
            if not source_ids:
                errors.append(f"{prefix}: capability {key} has no source_ids")
                continue
            for source_id in source_ids:
                if source_id not in seen_source_ids:
                    errors.append(f"{prefix}: capability {key} cites unknown source {source_id}")

        for key in mission.capability_sources:
            if key in SCALAR_CAPABILITY_KEYS or (optical and key == OPTICAL_CAPABILITY_KEY):
                continue
            if key.startswith("bands.") and key.split(".", 1)[1] in mission.bands:
                continue
            errors.append(f"{prefix}: capability_sources has unused key {key}")

    if errors:
        raise CatalogError("catalog integrity failure:\n  " + "\n  ".join(errors))


def load_catalog() -> Catalog:
    """Load and validate the packaged catalog."""
    missions_raw = _read_packaged_yaml("missions.yaml")
    sources_raw = _read_packaged_yaml("sources.yaml")

    catalog = Catalog(
        version=missions_raw["catalog_version"],
        missions=tuple(_parse_mission(entry) for entry in missions_raw.get("missions") or []),
        sources=_parse_sources(sources_raw),
    )
    validate_catalog(catalog)
    return catalog
