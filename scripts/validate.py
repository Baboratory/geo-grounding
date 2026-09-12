#!/usr/bin/env python3
"""Validate all data/**/*.yaml files against schema/*.schema.json, plus
cross-references:
- languageUsage[].languageCode against data/languages/*.yaml
- every sourceId (ethnicGroups, languageUsage, religions, legalConstraints,
  paymentMethodShares, businessRhythm.notableShutdownPeriods) against that
  same file's own sources[].id — enforces that every statistic cites an
  official source declared in the file.
- every distinct-regions[] entry has adminUnitCodes when hasSubdivisions=true
  (needed for IP-geolocation-based region lookup).
- every country has exactly one distinct-regions[] entry with code 'WHOLE'.
- every distinct-regions[] entry's 'code' matches the 'code' field inside
  the region file it points to, and that file actually exists.
- every non-'allYear' season used in a region's entertainment/
  traditionalDishes/traditionalClothing has a matching seasonCalendar
  entry, and seasonCalendar's months[] partition the year exactly (each
  of 1-12 appears in exactly one entry) — needed for
  usage_examples/python/get_data_by_ip.py to work.
- every timezone entry with observesDst=true has both dstUtcOffset and
  dstPeriod set, and every entry with observesDst=false has neither.
- governanceType/hasSubdivisions/iso3166_2_prefix agree with each other:
  federal/unitary-large implies hasSubdivisions=true and iso3166_2_prefix
  equal to alpha2; unitary-small/dependent-territory implies
  hasSubdivisions=false and iso3166_2_prefix=null. DESIGN.md and the
  schema document this as the rule, not just a convention some countries
  happen to follow -- this is what actually enforces it.

Requires: pyyaml, jsonschema[format] (pip install pyyaml "jsonschema[format]"
-- the [format] extra is what makes the schemas' declared "uri"/"date"
formats actually get checked, not just accepted as valid strings).
"""

import glob
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent

# Needed for the "uri"/"date" formats declared in the schemas to actually be
# checked -- jsonschema silently treats a format as always-valid if the
# optional package backing it (rfc3987, for "uri") isn't installed, rather
# than erroring. Install with `jsonschema[format]`, not bare `jsonschema`.
FORMAT_CHECKER = FormatChecker()


def load_schema(name: str) -> dict:
    with open(ROOT / "schema" / name) as f:
        schema = json.load(f)
    Draft7Validator.check_schema(schema)
    return schema


def validate_glob(pattern: str, schema: dict, error_count: int) -> int:
    validator = Draft7Validator(schema, format_checker=FORMAT_CHECKER)
    for path in sorted(glob.glob(str(ROOT / pattern))):
        with open(path) as f:
            data = yaml.safe_load(f)
        errs = list(validator.iter_errors(data))
        if errs:
            error_count += len(errs)
            print(f"FAIL {path}")
            for e in errs:
                print("   ", e.message, list(e.path))
        else:
            print(f"OK   {path}")
    return error_count


def validate_all() -> int:
    country_schema = load_schema("country.schema.json")
    region_schema = load_schema("region.schema.json")
    language_schema = load_schema("language.schema.json")

    error_count = 0
    error_count = validate_glob("data/countries/*/country.yaml", country_schema, error_count)
    error_count = validate_glob(
        "data/countries/*/distinct-regions/*.yaml", region_schema, error_count
    )
    error_count = validate_glob("data/languages/*.yaml", language_schema, error_count)

    known_language_codes = {Path(p).stem for p in glob.glob(str(ROOT / "data/languages/*.yaml"))}
    for path in sorted(glob.glob(str(ROOT / "data/countries/*/country.yaml"))):
        with open(path) as f:
            data = yaml.safe_load(f)
        for entry in data.get("languageUsage", []):
            code = entry["languageCode"]
            if code not in known_language_codes:
                error_count += 1
                print(
                    f"FAIL {path}: languageUsage references unknown languageCode '{code}' "
                    f"(no data/languages/{code}.yaml)"
                )

    def check_source_ids(path: str, data: dict) -> int:
        errs = 0
        known_source_ids = {s["id"] for s in data.get("sources", [])}
        for field in (
            "ethnicGroups",
            "languageUsage",
            "religions",
            "legalConstraints",
            "paymentMethodShares",
        ):
            for entry in data.get(field, []):
                source_id = entry.get("sourceId")
                if source_id and source_id not in known_source_ids:
                    errs += 1
                    print(
                        f"FAIL {path}: {field} entry references unknown sourceId '{source_id}' "
                        f"(not declared in this file's sources[])"
                    )
        for entry in data.get("businessRhythm", {}).get("notableShutdownPeriods", []):
            source_id = entry.get("sourceId")
            if source_id and source_id not in known_source_ids:
                errs += 1
                print(
                    f"FAIL {path}: businessRhythm.notableShutdownPeriods entry references "
                    f"unknown sourceId '{source_id}' (not declared in this file's sources[])"
                )
        return errs

    for path in sorted(glob.glob(str(ROOT / "data/countries/*/country.yaml"))):
        with open(path) as f:
            data = yaml.safe_load(f)
        error_count += check_source_ids(path, data)

    for path in sorted(glob.glob(str(ROOT / "data/countries/*/distinct-regions/*.yaml"))):
        with open(path) as f:
            data = yaml.safe_load(f)
        error_count += check_source_ids(path, data)

    for path in sorted(glob.glob(str(ROOT / "data/countries/*/country.yaml"))):
        with open(path) as f:
            data = yaml.safe_load(f)
        for tz in data.get("timezones", []):
            if tz.get("observesDst"):
                if not tz.get("dstUtcOffset") or not tz.get("dstPeriod"):
                    error_count += 1
                    print(
                        f"FAIL {path}: timezone '{tz.get('name')}' has observesDst=true but "
                        f"is missing dstUtcOffset and/or dstPeriod"
                    )
            elif tz.get("dstUtcOffset") or tz.get("dstPeriod"):
                error_count += 1
                print(
                    f"FAIL {path}: timezone '{tz.get('name')}' has observesDst=false but "
                    f"sets dstUtcOffset/dstPeriod anyway — remove them or set observesDst=true"
                )

    subdivided_types = {"federal", "unitary-large"}
    for path in sorted(glob.glob(str(ROOT / "data/countries/*/country.yaml"))):
        with open(path) as f:
            data = yaml.safe_load(f)
        governance_type = data.get("governanceType")
        if governance_type is None:
            continue  # optional field; nothing to cross-check against
        has_subdivisions = data.get("hasSubdivisions")
        prefix = data.get("iso3166_2_prefix")
        alpha2 = data.get("alpha2")
        should_have_subdivisions = governance_type in subdivided_types
        if has_subdivisions != should_have_subdivisions:
            error_count += 1
            print(
                f"FAIL {path}: governanceType '{governance_type}' implies "
                f"hasSubdivisions={should_have_subdivisions}, but it's {has_subdivisions}"
            )
        expected_prefix = alpha2 if should_have_subdivisions else None
        if prefix != expected_prefix:
            error_count += 1
            print(
                f"FAIL {path}: governanceType '{governance_type}' implies "
                f"iso3166_2_prefix={expected_prefix!r}, but it's {prefix!r}"
            )

    for path in sorted(glob.glob(str(ROOT / "data/countries/*/country.yaml"))):
        with open(path) as f:
            data = yaml.safe_load(f)
        entries = data.get("distinct-regions", [])

        if data.get("hasSubdivisions"):
            for entry in entries:
                if entry.get("code") == "WHOLE":
                    continue
                if not entry.get("adminUnitCodes"):
                    error_count += 1
                    print(
                        f"FAIL {path}: distinct-regions entry '{entry.get('code')}' is missing "
                        f"adminUnitCodes (required on non-WHOLE entries when "
                        f"hasSubdivisions=true, for IP-based lookup)"
                    )

        whole_entries = [e for e in entries if e.get("code") == "WHOLE"]
        if len(whole_entries) != 1:
            error_count += 1
            print(
                f"FAIL {path}: distinct-regions must contain exactly one 'WHOLE' entry "
                f"(found {len(whole_entries)}) — needed as the country-wide fallback for "
                f"usage_examples/python/get_data_by_ip.py, even when hasSubdivisions=true"
            )

        country_dir = Path(path).parent
        for entry in entries:
            region_path = country_dir / entry["file"]
            if not region_path.exists():
                error_count += 1
                print(
                    f"FAIL {path}: distinct-regions entry '{entry.get('code')}' points to "
                    f"'{entry['file']}', which does not exist"
                )
                continue
            with open(region_path) as f:
                region_data = yaml.safe_load(f)
            if region_data.get("code") != entry.get("code"):
                error_count += 1
                print(
                    f"FAIL {path}: distinct-regions entry has code '{entry.get('code')}' but "
                    f"'{entry['file']}' declares code '{region_data.get('code')}' "
                    f"— these must match"
                )

    for path in sorted(glob.glob(str(ROOT / "data/countries/*/distinct-regions/*.yaml"))):
        with open(path) as f:
            data = yaml.safe_load(f)

        used_seasons = set()
        for field in ("entertainment", "traditionalDishes", "traditionalClothing"):
            for entry in data.get(field, []):
                if entry["season"] != "allYear":
                    used_seasons.add(entry["season"])

        calendar = data.get("seasonCalendar", [])
        calendar_seasons = {e["season"] for e in calendar}

        missing = used_seasons - calendar_seasons
        if missing:
            error_count += 1
            print(
                f"FAIL {path}: season(s) {sorted(missing)} used in entertainment/traditionalDishes/"
                f"traditionalClothing but missing from seasonCalendar"
            )

        if calendar:
            month_owner: dict[int, str] = {}
            for entry in calendar:
                for month in entry["months"]:
                    if month in month_owner:
                        error_count += 1
                        print(
                            f"FAIL {path}: seasonCalendar assigns month {month} to both "
                            f"'{month_owner[month]}' and '{entry['season']}'"
                        )
                    else:
                        month_owner[month] = entry["season"]
            missing_months = set(range(1, 13)) - month_owner.keys()
            if missing_months:
                error_count += 1
                print(
                    f"FAIL {path}: seasonCalendar does not cover month(s) {sorted(missing_months)} "
                    f"(1-12 must partition exactly across all entries)"
                )

    print(f"\n{error_count} error(s)")
    return 1 if error_count else 0


if __name__ == "__main__":
    sys.exit(validate_all())
