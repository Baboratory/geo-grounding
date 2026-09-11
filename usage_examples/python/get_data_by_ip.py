#!/usr/bin/env python3
"""USAGE EXAMPLE (Python) — not core library code, see note below.

Given an already-resolved GeoIP result (country + optional subdivision) and,
optionally, a date, this demonstrates the full intended flow for answering
"what should we show this visitor right now":

  1. resolve_region(countryCode, subdivisionCode) -> which distinct-region
     file applies (exact regional match, or the country-wide WHOLE fallback).
  2. Load that region's YAML.
  3. current_season(region_data) -> "summer" / "winter" / "dry" / "wet" / ...
  4. current_content(region_data) -> only the entertainment/traditionalDishes/
     traditionalClothing items relevant right now (current season + allYear).
  5. get_data_by_ip(...) ties 1-4 together into one call.

Where the actual IP address is turned into {countryCode, subdivisionCode} is
NOT included here — that's a provider-specific reader (geoip2 for MaxMind,
maxminddb for DB-IP's .mmdb, or the IP2Location package; see README.md
"Palaikomi GeoIP šaltiniai"). Some readers (e.g. MaxMind's raw
subdivisions[0].iso_code) omit the country prefix ("BRE" not "FR-BRE") —
resolve_region() accepts either form.

IMPORTANT — this lives under usage_examples/, not scripts/: it is a
reference implementation of the intended logic, not something the live
baboratory.com website necessarily imports as-is. If the website's backend
is not Python, port resolve_region()/current_season() (each are short,
dependency-free aside from PyYAML) to that language instead of shelling out
to Python per request. scripts/validate.py and
scripts/generate_language_priority_conf.py are the only files meant to run
as project tooling (data QA, build-time artifact generation) regardless of
the website's backend language.

Design principle — this never guesses a default: if the country/region/
season can't be determined, it raises (UnknownLocationError /
NoSeasonCalendarError) rather than picking one. Deciding what to show an
unresolvable visitor is a product decision for the calling application.

Requires: pyyaml (pip install pyyaml)
"""

import argparse
import datetime
import glob
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent


class UnknownLocationError(LookupError):
    """Raised when resolve_region cannot determine a country/region for the
    given input. This is an expected, normal outcome (not a bug) for
    private/reserved IPs, VPNs, or GeoIP database misses — callers must
    catch it and decide their own fallback behavior."""


class NoSeasonCalendarError(LookupError):
    """Raised when a region has no seasonCalendar to determine the current
    season from — expected for regions whose seasonal fields use only
    'allYear' (no calendar is needed there). Callers must decide their own
    fallback (e.g. just show the allYear content, with no season-specific
    image)."""


def _load_country(country_code: str) -> dict | None:
    code = country_code.upper()
    candidates = glob.glob(str(ROOT / "data/countries/*/country.yaml"))
    for path in candidates:
        with open(path) as f:
            data = yaml.safe_load(f)
        if data["alpha2"] == code or data["alpha3"] == code:
            data["_path"] = path
            return data
    return None


def resolve_region(country_code: str | None, subdivision_code: str | None = None) -> dict:
    """Returns {"country": <alpha3>, "regionCode": <code>, "file": <path>,
    "matchedBy": "adminUnitCode" | "whole-country" | "whole-country-fallback"}.
    "whole-country" means hasSubdivisions=false (there was only ever one
    region). "whole-country-fallback" means hasSubdivisions=true but the
    visitor's specific subdivision isn't curated, so the generic
    country-wide WHOLE content was used instead — callers may want to show
    this distinction in the UI (e.g. "showing general France info").

    Raises UnknownLocationError if country_code is empty/None (GeoIP did not
    resolve a country at all) or isn't one of the 249 ISO 3166-1 entries in
    this dataset."""
    if not country_code:
        raise UnknownLocationError(
            "no country code given — GeoIP lookup did not resolve a country for this "
            "visitor (private/reserved IP, VPN, or a database miss are the usual causes)."
        )

    country = _load_country(country_code)
    if country is None:
        raise UnknownLocationError(
            f"'{country_code}' is not a country code covered by this dataset "
            f"(not one of the 249 ISO 3166-1 entries curated here)."
        )

    country_dir = Path(country["_path"]).parent
    regions = country["distinct-regions"]

    if country.get("hasSubdivisions") and subdivision_code:
        full_code = subdivision_code.upper()
        if "-" not in full_code:
            full_code = f"{country['alpha2']}-{full_code}"
        for region in regions:
            if full_code in [c.upper() for c in region.get("adminUnitCodes", [])]:
                return {
                    "country": country["alpha3"],
                    "regionCode": region["code"],
                    "file": str(country_dir / region["file"]),
                    "matchedBy": "adminUnitCode",
                }

    # No exact admin-unit match (either hasSubdivisions=false, no
    # subdivision_code given, or the subdivision isn't one of the curated
    # regions — e.g. FR-IDF isn't documented yet). Every country is
    # guaranteed exactly one 'WHOLE' entry (enforced by scripts/validate.py),
    # which we use as the country-wide fallback instead of an arbitrary
    # curated region — picking e.g. Brittany for a Paris visitor would
    # misrepresent them as Breton.
    whole = next((r for r in regions if r.get("code") == "WHOLE"), None)
    if whole is None:
        # Should be unreachable if the dataset passed scripts/validate.py.
        raise UnknownLocationError(
            f"'{country['alpha3']}' has no WHOLE entry in distinct-regions "
            f"— dataset is inconsistent, run scripts/validate.py"
        )

    return {
        "country": country["alpha3"],
        "regionCode": whole["code"],
        "file": str(country_dir / whole["file"]),
        "matchedBy": (
            "whole-country" if not country.get("hasSubdivisions") else "whole-country-fallback"
        ),
    }


def current_season(region_data: dict, on_date: datetime.date | None = None) -> str:
    """Returns the season label (e.g. "summer", "dry") that on_date (default:
    today) falls into for this region, per its seasonCalendar. Raises
    NoSeasonCalendarError if the region has no seasonCalendar."""
    calendar = region_data.get("seasonCalendar")
    if not calendar:
        raise NoSeasonCalendarError(
            f"region '{region_data.get('code')}' has no seasonCalendar — its seasonal "
            f"fields use only 'allYear', or the calendar hasn't been curated yet."
        )

    month = (on_date or datetime.date.today()).month
    for entry in calendar:
        if month in entry["months"]:
            return entry["season"]

    # Unreachable if the file passed scripts/validate.py (months[] must
    # partition 1-12 exactly), but don't silently guess if it didn't.
    raise NoSeasonCalendarError(
        f"region '{region_data.get('code')}' seasonCalendar does not cover month {month} "
        f"— run scripts/validate.py, the dataset is inconsistent."
    )


def current_content(region_data: dict, on_date: datetime.date | None = None) -> dict:
    """Returns {field_name: [items]} for entertainment/traditionalDishes/
    traditionalClothing, each filtered to allYear items plus (if a
    seasonCalendar exists) the items for the current season. If there is no
    seasonCalendar, only allYear items are returned for each field (no error
    — a missing calendar just means there is nothing season-specific to
    add, not that nothing can be shown)."""
    try:
        season = current_season(region_data, on_date)
    except NoSeasonCalendarError:
        season = None

    result = {}
    for field in ("entertainment", "traditionalDishes", "traditionalClothing"):
        items = []
        for entry in region_data.get(field, []):
            if entry["season"] == "allYear" or entry["season"] == season:
                items.extend(entry["items"])
        result[field] = items
    return result


def get_data_by_ip(
    country_code: str | None,
    subdivision_code: str | None = None,
    on_date: datetime.date | None = None,
) -> dict:
    """Ties resolve_region() + current_season()/current_content() together.
    Takes an already-resolved GeoIP {countryCode, subdivisionCode} pair (see
    module docstring for why the IP-to-that-pair step isn't included here).

    Returns {"country", "regionCode", "matchedBy", "season" (None if the
    region has no seasonCalendar), "content" (current_content() output)}.

    Raises UnknownLocationError if the country/region can't be resolved at
    all — there is nothing to return content for in that case, so unlike
    current_content()'s own graceful "no calendar -> allYear only" behavior,
    an unresolvable location is not something this function can paper over."""
    region_ref = resolve_region(country_code, subdivision_code)

    with open(region_ref["file"]) as f:
        region_data = yaml.safe_load(f)

    try:
        season = current_season(region_data, on_date)
    except NoSeasonCalendarError:
        season = None

    return {
        "country": region_ref["country"],
        "regionCode": region_ref["regionCode"],
        "matchedBy": region_ref["matchedBy"],
        "season": season,
        "content": current_content(region_data, on_date),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "country",
        nargs="?",
        default=None,
        help="ISO 3166-1 alpha-2 or alpha-3 code, e.g. FR or FRA. "
        "Omit to simulate a failed GeoIP lookup (no country determined).",
    )
    parser.add_argument(
        "subdivision",
        nargs="?",
        default=None,
        help="ISO 3166-2 subdivision code, full ('FR-BRE') or bare ('BRE')",
    )
    parser.add_argument("--date", help="YYYY-MM-DD to simulate (default: today)", default=None)
    args = parser.parse_args()

    on_date = datetime.date.fromisoformat(args.date) if args.date else None

    try:
        result = get_data_by_ip(args.country, args.subdivision, on_date)
    except UnknownLocationError as e:
        # Not a bug — this is the expected "I don't know" signal. The caller
        # (here, this CLI) is responsible for deciding what to do about it.
        print(f"unknown: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2, ensure_ascii=False))
