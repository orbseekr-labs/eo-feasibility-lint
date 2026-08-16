"""Catalog integrity (spec section 46) and capability access."""

from __future__ import annotations

import dataclasses

import pytest

from eo_feasibility_lint.catalog import (
    SUPPORTED_MISSION_IDS,
    CatalogError,
    load_catalog,
    validate_catalog,
)
from eo_feasibility_lint.models import BAND_FAMILIES, REASON_CODES


def replace_mission(catalog, mission_id, **changes):
    """Return a copy of the catalog with one mission altered."""
    missions = tuple(
        dataclasses.replace(mission, **changes) if mission.id == mission_id else mission
        for mission in catalog.missions
    )
    return dataclasses.replace(catalog, missions=missions)


# --- The shipped catalog --------------------------------------------------


def test_catalog_loads_and_validates():
    catalog = load_catalog()
    assert catalog.version == "2026-08-15.1"
    assert catalog.mission_ids() == (
        "sentinel-2",
        "sentinel-1-iw",
        "landsat-8",
        "landsat-9",
        "landsat-8-9",
    )


def test_every_supported_mission_is_present(catalog):
    assert set(catalog.mission_ids()) == set(SUPPORTED_MISSION_IDS)


def test_every_mission_cites_sources(catalog):
    for mission in catalog.missions:
        assert mission.source_ids, mission.id
        for source_id in mission.source_ids:
            assert catalog.source(source_id) is not None


def test_every_listed_band_family_has_provenance(catalog):
    for mission in catalog.missions:
        for family in mission.bands:
            assert mission.capability_sources.get(f"bands.{family}"), (mission.id, family)


def test_no_unknown_band_families(catalog):
    for mission in catalog.missions:
        assert set(mission.bands) <= set(BAND_FAMILIES), mission.id


def test_reason_codes_are_unique():
    codes = [reason.code for reason in REASON_CODES]
    assert len(codes) == len(set(codes))


def test_source_ids_are_unique(catalog):
    ids = [source.id for source in catalog.sources]
    assert len(ids) == len(set(ids))


# --- Documented capability values ----------------------------------------


def test_sentinel2_capabilities(catalog):
    mission = catalog.get("sentinel-2")
    assert mission.modalities == ("optical_multispectral",)
    assert mission.revisit_days == 5
    assert mission.swath_km == 290
    assert mission.all_weather is False
    assert mission.band_resolution_m("visible") == 10
    assert mission.band_resolution_m("red_edge") == 20
    assert mission.band_available("thermal_ir") is False
    assert mission.band_available("panchromatic") is False


def test_sentinel1_capabilities(catalog):
    mission = catalog.get("sentinel-1-iw")
    assert mission.modalities == ("sar_c_band",)
    assert mission.revisit_days == 6
    assert mission.swath_km == 250
    assert mission.all_weather is True
    assert mission.sar_nominal_resolution_m() == 20  # conservative: max(5, 20)
    assert mission.default_multispectral_gsd_m is None  # no optical payload


def test_landsat_capabilities(catalog):
    for mission_id in ("landsat-8", "landsat-9"):
        mission = catalog.get(mission_id)
        assert mission.revisit_days == 16
        assert mission.swath_km == 185
        assert mission.band_resolution_m("visible") == 30
        assert mission.band_resolution_m("panchromatic") == 15
        assert mission.band_resolution_m("thermal_ir") == 100


def test_landsat_combined_is_faster_but_same_sensors(catalog):
    combined = catalog.get("landsat-8-9")
    single = catalog.get("landsat-8")
    assert combined.revisit_days == 8
    assert combined.swath_km == single.swath_km
    assert combined.bands == single.bands


@pytest.mark.parametrize(
    ("mission_id", "expected"),
    [
        ("sentinel-2", 10),
        ("landsat-8", 30),
        ("landsat-9", 30),
        ("landsat-8-9", 30),
    ],
)
def test_default_multispectral_gsd_is_explicit_catalog_data(catalog, mission_id, expected):
    """Never derived from band ordering or a minimum; panchromatic is not used."""
    mission = catalog.get(mission_id)
    assert mission.default_multispectral_gsd_m == expected
    assert mission.default_multispectral_gsd_m != mission.band_resolution_m("panchromatic")
    assert mission.capability_sources["default_multispectral_gsd_m"]


def test_default_multispectral_gsd_required_for_optical_missions(catalog):
    with pytest.raises(CatalogError, match="has no default_multispectral_gsd_m"):
        validate_catalog(
            replace_mission(catalog, "sentinel-2", default_multispectral_gsd_m=None)
        )


def test_default_multispectral_gsd_rejected_for_non_optical_missions(catalog):
    with pytest.raises(CatalogError, match="non-optical mission"):
        validate_catalog(
            replace_mission(catalog, "sentinel-1-iw", default_multispectral_gsd_m=10)
        )


@pytest.mark.parametrize("value", [0, -1])
def test_invalid_default_multispectral_gsd_rejected(catalog, value):
    with pytest.raises(CatalogError, match="invalid default_multispectral_gsd_m"):
        validate_catalog(
            replace_mission(catalog, "sentinel-2", default_multispectral_gsd_m=value)
        )


def test_night_support_resolves_through_group_keys(catalog):
    sentinel2 = catalog.get("sentinel-2")
    assert sentinel2.night_support_for("visible") is False
    assert sentinel2.night_support_for("swir") is False

    sentinel1 = catalog.get("sentinel-1-iw")
    assert sentinel1.night_support_for("c_band_sar") is True

    landsat = catalog.get("landsat-8")
    assert landsat.night_support_for("thermal_ir") == "occasional"
    assert landsat.night_support_for("visible") is False


def test_every_available_family_states_night_support(catalog):
    """Missing metadata is a catalog defect, never an implicit false."""
    for mission in catalog.missions:
        for family in mission.available_families():
            assert mission.night_support_for(family) in (True, False, "occasional"), (
                mission.id,
                family,
            )


def test_unstated_night_support_is_not_false(catalog):
    """An unlisted family resolves to None, not to False."""
    landsat = catalog.get("landsat-8")
    assert landsat.night_support_for("red_edge") is None
    assert landsat.night_support_for("red_edge") is not False


def test_missing_night_support_for_available_family_is_rejected(catalog):
    mission = catalog.get("landsat-8")
    stripped = {k: v for k, v in mission.night_support.items() if k != "cirrus"}
    with pytest.raises(CatalogError, match="night support for cirrus is not stated"):
        validate_catalog(replace_mission(catalog, "landsat-8", night_support=stripped))


def test_provenance_never_falls_back_to_generic_mission_sources(catalog):
    mission = catalog.get("sentinel-1-iw")
    assert "coastal_aerosol" not in mission.bands
    assert mission.sources_for("bands.coastal_aerosol") == ()


def test_inventory_provenance_is_declared(catalog):
    for mission in catalog.missions:
        assert mission.modality_inventory_source_ids, mission.id
        assert mission.band_inventory_source_ids, mission.id
        for source_id in mission.modality_inventory_source_ids + (
            mission.band_inventory_source_ids
        ):
            assert catalog.source(source_id) is not None


@pytest.mark.parametrize(
    "field", ["modality_inventory_source_ids", "band_inventory_source_ids"]
)
def test_missing_inventory_provenance_is_rejected(catalog, field):
    with pytest.raises(CatalogError, match=f"has no {field}"):
        validate_catalog(replace_mission(catalog, "sentinel-2", **{field: ()}))


@pytest.mark.parametrize(
    "field", ["modality_inventory_source_ids", "band_inventory_source_ids"]
)
def test_unknown_inventory_source_is_rejected(catalog, field):
    with pytest.raises(CatalogError, match="cites unknown source"):
        validate_catalog(replace_mission(catalog, "sentinel-2", **{field: ("nasa-blog",)}))


# --- Every capability-dependent finding must be traceable to a source -----

#: One requirement per capability-dependent reason code, and the mission that
#: triggers it.
PROVENANCE_MATRIX = [
    ("EFL201", "sentinel-2", {"modality_any_of": ["sar_c_band"]}),
    ("EFL201", "sentinel-2", {"spatial": {"sar_max_resolution_m": 20}}),
    ("EFL202", "sentinel-2", {"spectral_bands_all_of": ["thermal_ir"]}),
    ("EFL202", "sentinel-1-iw", {"spectral_bands_all_of": ["coastal_aerosol"]}),
    (
        "EFL301",
        "landsat-8",
        {"spectral_bands_all_of": ["visible"], "spatial": {"optical_max_gsd_m": 10}},
    ),
    ("EFL301", "landsat-8", {"spatial": {"optical_max_gsd_m": 10}}),
    ("EFL302", "landsat-8", {"spatial": {"thermal_max_gsd_m": 50}}),
    ("EFL303", "sentinel-1-iw", {"spatial": {"sar_max_resolution_m": 10}}),
    ("EFL401", "sentinel-2", {"temporal": {"max_nominal_revisit_days": 1}}),
    ("EFL402", "sentinel-2", {"temporal": {"max_nominal_revisit_days": 5}}),
    ("EFL501", "sentinel-2", {"illumination": {"must_support_night": True}}),
    ("EFL502", "landsat-8", {"illumination": {"must_support_night": True}}),
    ("EFL601", "sentinel-2", {"weather": {"must_support_all_weather": True}}),
    ("EFL701", "sentinel-2", {"coverage": {"min_single_pass_swath_km": 400}}),
]


@pytest.mark.parametrize(("code", "mission_id", "sections"), PROVENANCE_MATRIX)
def test_capability_findings_cite_known_sources(catalog, result, code, mission_id, sections):
    outcome = result(mission_id, **sections)
    matching = [finding for finding in outcome.findings if finding.code == code]
    assert matching, f"{code} was not produced by {mission_id} / {sections}"
    for finding in matching:
        assert finding.source_ids, f"{code} carries no source_ids"
        for source_id in finding.source_ids:
            assert catalog.source(source_id) is not None, source_id


@pytest.mark.parametrize(
    ("code", "mission_id", "sections", "expected"),
    [
        ("EFL201", "sentinel-2", {"modality_any_of": ["sar_c_band"]}, "modality"),
        ("EFL201", "sentinel-2", {"spatial": {"sar_max_resolution_m": 20}}, "modality"),
        ("EFL202", "sentinel-2", {"spectral_bands_all_of": ["thermal_ir"]}, "band"),
        ("EFL202", "sentinel-1-iw", {"spectral_bands_all_of": ["nir"]}, "band"),
    ],
)
def test_absence_findings_cite_inventory_provenance(
    catalog, result, code, mission_id, sections, expected
):
    """A negative capability conclusion cites the designated inventory source."""
    mission = catalog.get(mission_id)
    inventory = (
        mission.modality_inventory_source_ids
        if expected == "modality"
        else mission.band_inventory_source_ids
    )
    finding = next(f for f in result(mission_id, **sections).findings if f.code == code)
    assert finding.source_ids == inventory


# --- Integrity violations must be rejected -------------------------------


def test_duplicate_mission_id_rejected(catalog):
    broken = dataclasses.replace(catalog, missions=(*catalog.missions, catalog.missions[0]))
    with pytest.raises(CatalogError, match="duplicate mission id"):
        validate_catalog(broken)


def test_duplicate_source_id_rejected(catalog):
    broken = dataclasses.replace(catalog, sources=(*catalog.sources, catalog.sources[0]))
    with pytest.raises(CatalogError, match="duplicate source id"):
        validate_catalog(broken)


def test_mission_without_sources_rejected(catalog):
    with pytest.raises(CatalogError, match="has no source_ids"):
        validate_catalog(replace_mission(catalog, "sentinel-2", source_ids=()))


def test_capability_without_sources_rejected(catalog):
    mission = catalog.get("sentinel-2")
    stripped = {
        key: value
        for key, value in mission.capability_sources.items()
        if key != "nominal_revisit"
    }
    with pytest.raises(CatalogError, match="capability nominal_revisit has no source_ids"):
        validate_catalog(replace_mission(catalog, "sentinel-2", capability_sources=stripped))


def test_unknown_band_family_rejected(catalog):
    mission = catalog.get("sentinel-2")
    bands = dict(mission.bands, lidar={"available": True, "resolution_m": 1})
    with pytest.raises(CatalogError, match="unknown band family"):
        validate_catalog(replace_mission(catalog, "sentinel-2", bands=bands))


@pytest.mark.parametrize("days", [0, -5, None, "five"])
def test_invalid_revisit_rejected(catalog, days):
    with pytest.raises(CatalogError, match="invalid nominal revisit"):
        validate_catalog(replace_mission(catalog, "sentinel-2", revisit_days=days))


def test_unknown_revisit_scope_rejected(catalog):
    with pytest.raises(CatalogError, match="unknown revisit scope"):
        validate_catalog(replace_mission(catalog, "sentinel-2", revisit_scope="someday"))


def test_negative_swath_rejected(catalog):
    with pytest.raises(CatalogError, match="invalid swath_km"):
        validate_catalog(replace_mission(catalog, "sentinel-2", swath_km=-1))


def test_invalid_band_resolution_rejected(catalog):
    mission = catalog.get("sentinel-2")
    bands = dict(mission.bands, visible={"available": True, "resolution_m": 0})
    with pytest.raises(CatalogError, match="invalid resolution_m"):
        validate_catalog(replace_mission(catalog, "sentinel-2", bands=bands))


def test_invalid_night_support_value_rejected(catalog):
    with pytest.raises(CatalogError, match="invalid night_support value"):
        validate_catalog(
            replace_mission(catalog, "sentinel-2", night_support={"reflected_optical": "maybe"})
        )


def test_unknown_source_reference_rejected(catalog):
    with pytest.raises(CatalogError, match="unknown source id"):
        validate_catalog(replace_mission(catalog, "sentinel-2", source_ids=("nasa-blog",)))
