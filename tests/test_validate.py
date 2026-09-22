"""Regression tests for scripts/validate.py's rules -- schema conformance
plus the cross-file checks JSON Schema alone can't express (source-id
resolution, the WHOLE-region invariant, season-calendar partitioning,
governanceType/hasSubdivisions/iso3166_2_prefix agreement, etc., see
validate.py's own module docstring for the full list).

Each test builds a minimal, otherwise-valid fixture tree (real schema/
files copied in, so these exercise the actual project schema -- not a
decoupled copy that could drift from it), breaks exactly one thing, and
checks validate_all() catches it. validate_all()/load_schema()/
validate_glob() all take a `root` parameter for exactly this reason:
so a throwaway fixture directory can stand in for this repo's own data/
without a subprocess or any of this repo's real data files.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import validate  # noqa: E402


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def _minimal_country(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "alpha3": "ZZZ",
        "alpha2": "ZZ",
        "name": {"eng": "Testland", "local": [{"languageCode": "zzz", "value": "Testland"}]},
        "flagEmoji": "\U0001f3f3",
        "isSovereign": True,
        "governanceType": "unitary-small",
        "iso3166_2_prefix": None,
        "hasSubdivisions": False,
        "languageUsage": [
            {
                "languageCode": "zzz",
                "domain": "official",
                "speakersShare": 1.0,
                "sourceId": "zzz-law",
            },
        ],
        "timezones": [
            {"name": "Etc/UTC", "standardUtcOffset": "UTC+0", "observesDst": False},
        ],
        "currency": {"code": "ZZZ", "symbol": "Z", "name": "Testcoin"},
        "distinct-regions": [
            {"code": "WHOLE", "file": "distinct-regions/whole.yaml"},
        ],
        "sources": [
            {
                "id": "zzz-law",
                "name": "Test Law",
                "publisher": "Test Publisher",
                "url": "https://example.com/law",
                "accessedDate": "2026-01-01",
                "note": "Test source.",
            }
        ],
    }
    base.update(overrides)
    return base


def _minimal_region(code: str = "WHOLE", **overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "code": code,
        "name": {"eng": "Testland", "local": [{"languageCode": "zzz", "value": "Testland"}]},
    }
    base.update(overrides)
    return base


def _minimal_language() -> dict[str, Any]:
    return {"code": "zzz", "name": {"eng": "Testish", "local": "Testish"}}


def _fixture_root(tmp_path: Path) -> Path:
    root = tmp_path / "fixture"
    shutil.copytree(ROOT / "schema", root / "schema")
    return root


def build_valid_root(tmp_path: Path, country: dict[str, Any] | None = None) -> Path:
    """A minimal, unitary-small (WHOLE-only) country -- schema-valid and
    rule-valid as-is, for tests that mutate exactly one thing off of it."""
    root = _fixture_root(tmp_path)
    _write_yaml(root / "data/countries/ZZZ/country.yaml", country or _minimal_country())
    _write_yaml(root / "data/countries/ZZZ/distinct-regions/whole.yaml", _minimal_region())
    _write_yaml(root / "data/languages/zzz.yaml", _minimal_language())
    return root


def build_valid_subdivided_root(tmp_path: Path) -> Path:
    """A minimal federal-style country with one real region (ZZ-AA) plus
    the mandatory WHOLE fallback -- for rules that only apply to
    subdivided countries (adminUnitCodes prefixes/uniqueness, region-file
    cross-references, duplicate distinct-regions codes, ...)."""
    root = _fixture_root(tmp_path)
    country = _minimal_country(
        governanceType="federal",
        hasSubdivisions=True,
        iso3166_2_prefix="ZZ",
        regionCoverage={
            "tier": "first-level",
            "totalUnits": 4,
            "status": "partial",
            "gapReason": "Only ZZ-AA curated; the other three have their own official "
            "language (trigger 1) and are queued.",
        },
        **{
            "distinct-regions": [
                {"code": "ZZ-AA", "file": "distinct-regions/aa.yaml", "adminUnitCodes": ["ZZ-AA"]},
                {"code": "WHOLE", "file": "distinct-regions/whole.yaml"},
            ]
        },
    )
    _write_yaml(root / "data/countries/ZZZ/country.yaml", country)
    _write_yaml(root / "data/countries/ZZZ/distinct-regions/whole.yaml", _minimal_region())
    _write_yaml(root / "data/countries/ZZZ/distinct-regions/aa.yaml", _minimal_region("ZZ-AA"))
    _write_yaml(root / "data/languages/zzz.yaml", _minimal_language())
    return root


def run(root: Path) -> int:
    return validate.validate_all(root)


# --- baseline ----------------------------------------------------------


def test_valid_unitary_small_fixture_has_zero_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_root(tmp_path)
    assert run(root) == 0
    assert "0 error(s)" in capsys.readouterr().out


def test_valid_subdivided_fixture_has_zero_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_subdivided_root(tmp_path)
    assert run(root) == 0
    assert "0 error(s)" in capsys.readouterr().out


# --- JSON Schema conformance (incl. the format-checker extra) ----------


def test_schema_rejects_invalid_uri_format(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    country = _minimal_country()
    country["sources"][0]["url"] = "not a url"
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    # Regression guard for the earlier "uri" format silently passing
    # anything without the jsonschema[format]/rfc3987 extra installed.
    assert "is not a 'uri'" in capsys.readouterr().out


def test_schema_rejects_missing_required_field(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    country = _minimal_country()
    del country["currency"]
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0


# --- sourceId resolution -------------------------------------------------


def test_language_usage_references_unknown_source_id(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    country = _minimal_country()
    country["languageUsage"][0]["sourceId"] = "does-not-exist"
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    assert "unknown sourceId" in capsys.readouterr().out


def test_duplicate_sources_id_within_file(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    country = _minimal_country()
    country["sources"].append(dict(country["sources"][0]))  # same id, duplicated
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    assert "duplicate sources[].id" in capsys.readouterr().out


def test_business_rhythm_source_ids_unknown_reference(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    country = _minimal_country()
    country["businessRhythm"] = {"restDays": [], "sourceIds": ["ghost-source"]}
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    assert "businessRhythm.sourceIds references unknown sourceId" in capsys.readouterr().out


def test_business_rhythm_source_ids_duplicate_in_list(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    country = _minimal_country()
    country["businessRhythm"] = {"restDays": [], "sourceIds": ["zzz-law", "zzz-law"]}
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    assert "lists 'zzz-law' more than once" in capsys.readouterr().out


# --- language-code / language-file rules --------------------------------


def test_language_usage_references_unknown_language_code(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    country = _minimal_country()
    country["languageUsage"][0]["languageCode"] = "xxx"
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    assert "unknown languageCode" in capsys.readouterr().out


def test_language_file_code_must_match_filename(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_root(tmp_path)
    _write_yaml(root / "data/languages/zzz.yaml", {**_minimal_language(), "code": "yyy"})
    assert run(root) != 0
    assert "filename says 'zzz'" in capsys.readouterr().out


# --- WHOLE-region invariant ----------------------------------------------


def test_missing_whole_region_is_rejected(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    root = build_valid_subdivided_root(tmp_path)
    country_path = root / "data/countries/ZZZ/country.yaml"
    data = yaml.safe_load(country_path.read_text())
    data["distinct-regions"] = [e for e in data["distinct-regions"] if e["code"] != "WHOLE"]
    _write_yaml(country_path, data)
    assert run(root) != 0
    assert "exactly one 'WHOLE' entry" in capsys.readouterr().out


def test_duplicate_whole_region_is_rejected(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    root = build_valid_subdivided_root(tmp_path)
    country_path = root / "data/countries/ZZZ/country.yaml"
    data = yaml.safe_load(country_path.read_text())
    data["distinct-regions"].append({"code": "WHOLE", "file": "distinct-regions/whole.yaml"})
    _write_yaml(country_path, data)
    assert run(root) != 0
    out = capsys.readouterr().out
    assert "exactly one 'WHOLE' entry" in out
    assert "distinct-regions code 'WHOLE' appears more than once" in out


def test_has_subdivisions_false_forbids_extra_regions(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    country = _minimal_country()
    country["distinct-regions"].append({"code": "ZZ-AA", "file": "distinct-regions/aa.yaml"})
    root = build_valid_root(tmp_path, country)
    _write_yaml(root / "data/countries/ZZZ/distinct-regions/aa.yaml", _minimal_region("ZZ-AA"))
    assert run(root) != 0
    assert "hasSubdivisions=false but distinct-regions has 2 entries" in capsys.readouterr().out


# --- region-code / adminUnitCodes rules -----------------------------------


def test_region_code_must_share_country_alpha2_prefix(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_subdivided_root(tmp_path)
    country_path = root / "data/countries/ZZZ/country.yaml"
    data = yaml.safe_load(country_path.read_text())
    data["distinct-regions"][0] = {
        "code": "XX-AA",
        "file": "distinct-regions/aa.yaml",
        "adminUnitCodes": ["XX-AA"],
    }
    _write_yaml(country_path, data)
    _write_yaml(root / "data/countries/ZZZ/distinct-regions/aa.yaml", _minimal_region("XX-AA"))
    assert run(root) != 0
    assert "doesn't start with this country's own alpha2 prefix" in capsys.readouterr().out


def test_admin_unit_codes_must_share_country_alpha2_prefix(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_subdivided_root(tmp_path)
    country_path = root / "data/countries/ZZZ/country.yaml"
    data = yaml.safe_load(country_path.read_text())
    data["distinct-regions"][0]["adminUnitCodes"] = ["XX-AA"]
    _write_yaml(country_path, data)
    assert run(root) != 0
    assert "adminUnitCode 'XX-AA' on region 'ZZ-AA'" in capsys.readouterr().out


def test_admin_unit_codes_must_be_unique_across_regions(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_subdivided_root(tmp_path)
    country_path = root / "data/countries/ZZZ/country.yaml"
    data = yaml.safe_load(country_path.read_text())
    data["distinct-regions"].insert(
        1, {"code": "ZZ-BB", "file": "distinct-regions/bb.yaml", "adminUnitCodes": ["ZZ-AA"]}
    )
    _write_yaml(country_path, data)
    _write_yaml(root / "data/countries/ZZZ/distinct-regions/bb.yaml", _minimal_region("ZZ-BB"))
    assert run(root) != 0
    assert "used by both 'ZZ-AA' and 'ZZ-BB'" in capsys.readouterr().out


def test_distinct_regions_code_must_be_unique(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_subdivided_root(tmp_path)
    country_path = root / "data/countries/ZZZ/country.yaml"
    data = yaml.safe_load(country_path.read_text())
    data["distinct-regions"].insert(1, dict(data["distinct-regions"][0]))
    _write_yaml(country_path, data)
    assert run(root) != 0
    assert "distinct-regions code 'ZZ-AA' appears more than once" in capsys.readouterr().out


def test_distinct_regions_entry_missing_admin_unit_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_subdivided_root(tmp_path)
    country_path = root / "data/countries/ZZZ/country.yaml"
    data = yaml.safe_load(country_path.read_text())
    del data["distinct-regions"][0]["adminUnitCodes"]
    _write_yaml(country_path, data)
    assert run(root) != 0
    assert "missing adminUnitCodes" in capsys.readouterr().out


def test_distinct_regions_file_must_exist(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    root = build_valid_subdivided_root(tmp_path)
    (root / "data/countries/ZZZ/distinct-regions/aa.yaml").unlink()
    assert run(root) != 0
    assert "which does not exist" in capsys.readouterr().out


def test_distinct_regions_code_must_match_region_file_code(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_subdivided_root(tmp_path)
    _write_yaml(
        root / "data/countries/ZZZ/distinct-regions/aa.yaml", _minimal_region("ZZ-SOMETHING-ELSE")
    )
    assert run(root) != 0
    assert "these must match" in capsys.readouterr().out


# --- seasonCalendar partitioning -----------------------------------------


def test_season_used_but_missing_from_calendar(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_root(tmp_path)
    region = _minimal_region()
    region["entertainment"] = [{"season": "summer", "items": ["Something"]}]
    region["seasonCalendar"] = [{"season": "winter", "months": list(range(1, 13))}]
    _write_yaml(root / "data/countries/ZZZ/distinct-regions/whole.yaml", region)
    assert run(root) != 0
    assert "missing from seasonCalendar" in capsys.readouterr().out


def test_season_calendar_months_cannot_overlap(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_root(tmp_path)
    region = _minimal_region()
    region["seasonCalendar"] = [
        {"season": "summer", "months": [6, 7, 8]},
        {"season": "winter", "months": [8, 9, 10, 11, 12, 1, 2, 3, 4, 5]},
    ]
    _write_yaml(root / "data/countries/ZZZ/distinct-regions/whole.yaml", region)
    assert run(root) != 0
    assert "assigns month 8 to both" in capsys.readouterr().out


def test_season_calendar_must_cover_all_twelve_months(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_root(tmp_path)
    region = _minimal_region()
    region["seasonCalendar"] = [{"season": "summer", "months": [6, 7, 8]}]
    _write_yaml(root / "data/countries/ZZZ/distinct-regions/whole.yaml", region)
    assert run(root) != 0
    assert "does not cover month(s)" in capsys.readouterr().out


# --- DST consistency -------------------------------------------------------


def test_dst_true_requires_offset_and_period(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    country = _minimal_country()
    country["timezones"] = [{"name": "Etc/UTC", "standardUtcOffset": "UTC+0", "observesDst": True}]
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    assert "missing dstUtcOffset and/or dstPeriod" in capsys.readouterr().out


def test_dst_false_forbids_offset_and_period(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    country = _minimal_country()
    country["timezones"] = [
        {
            "name": "Etc/UTC",
            "standardUtcOffset": "UTC+0",
            "observesDst": False,
            "dstUtcOffset": "UTC+1",
            "dstPeriod": "Some period.",
        }
    ]
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    assert "sets dstUtcOffset/dstPeriod anyway" in capsys.readouterr().out


# --- governanceType / hasSubdivisions / iso3166_2_prefix agreement --------


def test_federal_requires_has_subdivisions_true(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    country = _minimal_country(governanceType="federal")  # hasSubdivisions still False
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    assert "implies hasSubdivisions=True" in capsys.readouterr().out


def test_unitary_small_forbids_iso3166_2_prefix(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    country = _minimal_country(iso3166_2_prefix="ZZ")  # unitary-small, hasSubdivisions False
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    assert "implies iso3166_2_prefix=None" in capsys.readouterr().out


def test_federal_iso3166_2_prefix_must_equal_alpha2(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_subdivided_root(tmp_path)
    country_path = root / "data/countries/ZZZ/country.yaml"
    data = yaml.safe_load(country_path.read_text())
    data["iso3166_2_prefix"] = "XX"
    _write_yaml(country_path, data)
    assert run(root) != 0
    assert "implies iso3166_2_prefix='ZZ'" in capsys.readouterr().out


# --- regionCoverage: the check aimed at data that isn't there ----------


def _mutate_coverage(root: Path, **changes: Any) -> None:
    """Apply changes to the fixture's regionCoverage; None deletes a key."""
    country_path = root / "data/countries/ZZZ/country.yaml"
    data = yaml.safe_load(country_path.read_text())
    if changes.get("_drop"):
        data.pop("regionCoverage", None)
    else:
        for key, value in changes.items():
            if value is None:
                data["regionCoverage"].pop(key, None)
            else:
                data["regionCoverage"][key] = value
    _write_yaml(country_path, data)


def test_subdivided_country_requires_region_coverage(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    root = build_valid_subdivided_root(tmp_path)
    _mutate_coverage(root, _drop=True)
    assert run(root) != 0
    assert "requires a regionCoverage block" in capsys.readouterr().out


def test_unsubdivided_country_forbids_region_coverage(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    country = _minimal_country(
        regionCoverage={"tier": "first-level", "totalUnits": 3, "status": "complete"}
    )
    root = build_valid_root(tmp_path, country)
    assert run(root) != 0
    assert "hasSubdivisions=false" in capsys.readouterr().out


def test_total_first_level_units_cannot_be_below_curated_count(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """Catches the specific mistake of filling in the curated count where
    the country's real ISO 3166-2 count belongs -- which would defeat the
    whole point of the field by making every country look complete."""
    root = build_valid_subdivided_root(tmp_path)
    country_path = root / "data/countries/ZZZ/country.yaml"
    data = yaml.safe_load(country_path.read_text())
    data["distinct-regions"].insert(
        1, {"code": "ZZ-BB", "file": "distinct-regions/bb.yaml", "adminUnitCodes": ["ZZ-BB"]}
    )
    data["regionCoverage"]["totalUnits"] = 1  # two curated, "one" unit total
    _write_yaml(country_path, data)
    _write_yaml(root / "data/countries/ZZZ/distinct-regions/bb.yaml", _minimal_region("ZZ-BB"))
    assert run(root) != 0
    assert "is smaller than the 2 curated region(s)" in capsys.readouterr().out


def test_partial_status_requires_gap_reason(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    root = build_valid_subdivided_root(tmp_path)
    _mutate_coverage(root, gapReason=None)
    assert run(root) != 0
    assert "requires gapReason" in capsys.readouterr().out


def test_complete_status_forbids_gap_reason(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    root = build_valid_subdivided_root(tmp_path)
    _mutate_coverage(root, status="complete")  # gapReason still present
    assert run(root) != 0
    assert "must not carry a" in capsys.readouterr().out
