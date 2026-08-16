"""Requirement validation, plus JSON Schema / validator synchronisation.

The published JSON Schemas are documentation, not runtime code. These tests keep
them honest.
"""

from __future__ import annotations

import json

import pytest
import yaml

from conftest import SCHEMAS_DIR, make_document
from eo_feasibility_lint import loader
from eo_feasibility_lint.catalog import SUPPORTED_MISSION_IDS
from eo_feasibility_lint.loader import RequirementError, load_requirement, parse_requirement
from eo_feasibility_lint.models import (
    BAND_FAMILIES,
    MODALITIES,
    OUTPUT_KINDS,
    SCHEMA_VERSION,
    VERDICTS,
    Finding,
)


@pytest.fixture(scope="module")
def requirement_schema():
    return json.loads((SCHEMAS_DIR / "requirement.schema.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report_schema():
    return json.loads((SCHEMAS_DIR / "report.schema.json").read_text(encoding="utf-8"))


def parse(document):
    return parse_requirement(document, SUPPORTED_MISSION_IDS)


# --- Validation behaviour -------------------------------------------------


def test_minimal_document_parses():
    requirement = parse(make_document())
    assert requirement.name == "test-requirement"
    assert requirement.output_kind == "instrument_measurement"
    assert requirement.candidate_missions is None


def test_schema_version_must_be_0_1():
    document = make_document()
    document["schema_version"] = "0.2"
    with pytest.raises(RequirementError, match="schema_version"):
        parse(document)


def test_schema_version_is_required():
    document = make_document()
    del document["schema_version"]
    with pytest.raises(RequirementError, match="schema_version is required"):
        parse(document)


@pytest.mark.parametrize("name", ["", "x" * 101])
def test_name_length_bounds(name):
    document = make_document()
    document["name"] = name
    with pytest.raises(RequirementError, match="name"):
        parse(document)


def test_objective_is_never_interpreted():
    document = make_document()
    document["objective"] = "measure parking lot traffic every day with thermal at night"
    requirement = parse(document)
    assert requirement.objective == document["objective"]
    # Nothing was extracted from the sentence.
    assert not requirement.has_testable_requirements()
    assert requirement.modality_any_of == ()
    assert requirement.must_support_night is None


def test_output_kind_is_required():
    document = make_document()
    del document["requirements"]["output"]
    with pytest.raises(RequirementError, match="output"):
        parse(document)


def test_unknown_output_kind_rejected():
    document = make_document(output="revenue")
    with pytest.raises(RequirementError, match=r"output\.kind"):
        parse(document)


def test_unknown_top_level_key_rejected():
    document = make_document()
    document["aoi"] = {"lat": 0, "lon": 0}
    with pytest.raises(RequirementError, match="unknown key"):
        parse(document)


def test_unknown_requirement_section_rejected():
    document = make_document()
    document["requirements"]["orbit"] = {"altitude_km": 700}
    with pytest.raises(RequirementError, match="unknown key"):
        parse(document)


def test_unknown_spatial_key_rejected():
    with pytest.raises(RequirementError, match="unknown key"):
        parse(make_document(spatial={"max_gsd_m": 10}))


def test_unknown_band_family_rejected():
    with pytest.raises(RequirementError, match="unknown value"):
        parse(make_document(spectral_bands_all_of=["hyperspectral"]))


def test_unknown_mission_rejected():
    with pytest.raises(RequirementError, match="unknown value"):
        parse(make_document(missions=["worldview-3"]))


def test_duplicate_band_family_rejected():
    with pytest.raises(RequirementError, match="duplicate"):
        parse(make_document(spectral_bands_all_of=["visible", "visible"]))


@pytest.mark.parametrize("value", [0, -1, "10", True])
def test_non_positive_spatial_values_rejected(value):
    with pytest.raises(RequirementError, match="positive number"):
        parse(make_document(spatial={"optical_max_gsd_m": value}))


def test_non_boolean_illumination_rejected():
    with pytest.raises(RequirementError, match="true or false"):
        parse(make_document(illumination={"must_support_night": "yes"}))


def test_integer_inputs_stay_integers():
    requirement = parse(make_document(spatial={"optical_max_gsd_m": 10}))
    assert requirement.optical_max_gsd_m == 10
    assert isinstance(requirement.optical_max_gsd_m, int)


def test_has_testable_requirements_ignores_negative_flags():
    requirement = parse(
        make_document(
            illumination={"must_support_night": False},
            weather={"must_support_all_weather": False},
        )
    )
    assert not requirement.has_testable_requirements()


def test_has_testable_requirements_counts_positive_flags():
    requirement = parse(make_document(illumination={"must_support_night": True}))
    assert requirement.has_testable_requirements()


# --- File loading ---------------------------------------------------------


def test_json_requirement_file(tmp_path):
    path = tmp_path / "requirement.json"
    path.write_text(json.dumps(make_document()), encoding="utf-8")
    assert load_requirement(path, SUPPORTED_MISSION_IDS).name == "test-requirement"


def test_unsupported_extension_rejected(tmp_path):
    path = tmp_path / "requirement.toml"
    path.write_text("name = 'x'", encoding="utf-8")
    with pytest.raises(RequirementError, match="unsupported file type"):
        load_requirement(path, SUPPORTED_MISSION_IDS)


def test_missing_file_rejected(tmp_path):
    with pytest.raises(RequirementError, match="cannot be read"):
        load_requirement(tmp_path / "absent.yaml", SUPPORTED_MISSION_IDS)


def test_empty_file_rejected(tmp_path):
    path = tmp_path / "requirement.yaml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(RequirementError, match="empty"):
        load_requirement(path, SUPPORTED_MISSION_IDS)


def test_yaml_is_parsed_safely(tmp_path):
    """No arbitrary object construction from a requirement document."""
    path = tmp_path / "requirement.yaml"
    path.write_text("!!python/object/apply:os.system ['echo pwned']\n", encoding="utf-8")
    with pytest.raises(RequirementError, match="cannot be parsed"):
        load_requirement(path, SUPPORTED_MISSION_IDS)


def test_strict_loader_is_a_safe_loader():
    assert issubclass(loader.StrictSafeLoader, yaml.SafeLoader)


# --- Duplicate mapping keys are ambiguous, so they are rejected -------------


DUPLICATE_YAML = """\
schema_version: "0.1"
name: duplicate-keys
requirements:
  temporal:
    max_nominal_revisit_days: 5
    max_nominal_revisit_days: 10
  output:
    kind: instrument_measurement
"""


def test_duplicate_yaml_key_is_rejected(tmp_path):
    path = tmp_path / "requirement.yaml"
    path.write_text(DUPLICATE_YAML, encoding="utf-8")
    with pytest.raises(RequirementError, match="duplicate key"):
        load_requirement(path, SUPPORTED_MISSION_IDS)


def test_duplicate_yaml_key_is_not_last_value_wins(tmp_path):
    """PyYAML would silently keep 10. That ambiguity must never be interpreted."""
    path = tmp_path / "requirement.yaml"
    path.write_text(DUPLICATE_YAML, encoding="utf-8")
    with pytest.raises(RequirementError):
        load_requirement(path, SUPPORTED_MISSION_IDS)
    assert yaml.safe_load(DUPLICATE_YAML)["requirements"]["temporal"] == {
        "max_nominal_revisit_days": 10
    }


@pytest.mark.parametrize(
    "document",
    [
        'schema_version: "0.1"\nschema_version: "0.1"\nname: x\n',
        'schema_version: "0.1"\nname: x\nname: y\n',
        'name: x\nrequirements:\n  output:\n    kind: a\n    kind: b\n',
    ],
)
def test_duplicate_keys_rejected_at_every_level(tmp_path, document):
    path = tmp_path / "requirement.yaml"
    path.write_text(document, encoding="utf-8")
    with pytest.raises(RequirementError, match="duplicate key"):
        load_requirement(path, SUPPORTED_MISSION_IDS)


def test_duplicate_json_key_is_rejected(tmp_path):
    path = tmp_path / "requirement.json"
    path.write_text(
        '{"schema_version": "0.1", "name": "a", "name": "b", "requirements": {}}',
        encoding="utf-8",
    )
    with pytest.raises(RequirementError, match="duplicate key"):
        load_requirement(path, SUPPORTED_MISSION_IDS)


def test_distinct_keys_still_load(tmp_path):
    path = tmp_path / "requirement.yaml"
    path.write_text(yaml.safe_dump(make_document(), sort_keys=False), encoding="utf-8")
    assert load_requirement(path, SUPPORTED_MISSION_IDS).name == "test-requirement"


# --- Schema / validator synchronisation -----------------------------------


def test_requirement_schema_top_level_keys(requirement_schema):
    assert tuple(requirement_schema["properties"]) == loader.TOP_LEVEL_KEYS
    assert requirement_schema["properties"]["schema_version"]["const"] == SCHEMA_VERSION
    assert requirement_schema["properties"]["name"]["maxLength"] == loader.NAME_MAX_LENGTH
    assert requirement_schema["properties"]["name"]["minLength"] == loader.NAME_MIN_LENGTH
    assert requirement_schema["additionalProperties"] is False


def test_requirement_schema_sections(requirement_schema):
    requirements = requirement_schema["properties"]["requirements"]
    assert tuple(requirements["properties"]) == loader.REQUIREMENT_KEYS
    section_keys = {
        "spatial": loader.SPATIAL_KEYS,
        "temporal": loader.TEMPORAL_KEYS,
        "illumination": loader.ILLUMINATION_KEYS,
        "weather": loader.WEATHER_KEYS,
        "coverage": loader.COVERAGE_KEYS,
        "output": loader.OUTPUT_KEYS,
    }
    for section, expected in section_keys.items():
        node = requirements["properties"][section]
        assert tuple(node["properties"]) == expected, section
        assert node["additionalProperties"] is False, section


def test_requirement_schema_enums(requirement_schema):
    requirements = requirement_schema["properties"]["requirements"]["properties"]
    assert tuple(requirement_schema["properties"]["candidate_missions"]["items"]["enum"]) == (
        SUPPORTED_MISSION_IDS
    )
    assert tuple(requirements["modality_any_of"]["items"]["enum"]) == MODALITIES
    assert tuple(requirements["spectral_bands_all_of"]["items"]["enum"]) == BAND_FAMILIES
    assert tuple(requirements["output"]["properties"]["kind"]["enum"]) == OUTPUT_KINDS


def test_report_schema_matches_models(report_schema):
    assert tuple(report_schema["$defs"]["verdict"]["enum"]) == VERDICTS
    finding_fields = tuple(Finding("EFL901", "UNKNOWN", "", "").to_dict())
    assert tuple(report_schema["$defs"]["finding"]["properties"]) == finding_fields
    assert tuple(report_schema["$defs"]["finding"]["required"]) == finding_fields
