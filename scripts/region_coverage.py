#!/usr/bin/env python3
"""Report how much of each country's real subdivision list is curated.

This answers the one question scripts/validate.py structurally cannot: not
"is what's here correct?" but "is anything missing?" A country with four
curated regions out of eighty-five validates exactly as cleanly as one with
four out of four -- the absent files raise nothing, because WHOLE answers in
their place. So this reads the real ISO 3166-2 first-level subdivision list
and prints it next to what the repo actually contains.

It is a reporting tool, not a gate: whether an uncurated subdivision *should*
have been curated depends on DESIGN.md's five coverage triggers (own
official/recognized language, different plurality religion, own law on
something modeled here, different time zone, different Koppen class), and
those need a human or an audit to assess. What this gives you is the list to
assess, and the numbers to check each country's declared
regionCoverage.totalUnits against.

Requires: pyyaml, pycountry (pip install -e ".[dev]"). Deliberately not
imported by validate.py, which stays on pyyaml + jsonschema only so that
anyone can run the validator without pulling in an ISO database.

Usage:
    python3 scripts/region_coverage.py            # every country, worst gaps first
    python3 scripts/region_coverage.py RUS IND    # just these
    python3 scripts/region_coverage.py --undeclared-only
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import pycountry
import yaml

ROOT = Path(__file__).resolve().parent.parent

# A first-level subdivision that is a dependent territory this dataset
# already gives its own separate data/countries/<ALPHA3>/ entry -- per
# DESIGN.md's "full ISO 3166-1 coverage, dependent territories included as
# their own entries" rule. These can never be curated a second time as a
# region of the parent (that would duplicate, not add, content), and they
# are not an open gap either: they are covered, just by a sibling country
# entry rather than a distinct-regions[] file. See DESIGN.md's coverage
# floor for the full explanation. This is a closed, verified list, not a
# pattern to extend by guessing -- checked against the real directory at
# runtime below, so a stale or wrong entry here fails loudly rather than
# silently miscounting.
SIBLING_COUNTRY_ENTRIES: dict[str, dict[str, str]] = {
    "CHN": {"CN-HK": "HKG", "CN-MO": "MAC", "CN-TW": "TWN"},
    "FRA": {
        "FR-971": "GLP",
        "FR-972": "MTQ",
        "FR-973": "GUF",
        "FR-974": "REU",
        "FR-976": "MYT",
        "FR-BL": "BLM",
        "FR-MF": "MAF",
        "FR-NC": "NCL",
        "FR-PF": "PYF",
        "FR-PM": "SPM",
        "FR-TF": "ATF",
        "FR-WF": "WLF",
    },
    "USA": {
        "US-AS": "ASM",
        "US-GU": "GUM",
        "US-MP": "MNP",
        "US-PR": "PRI",
        "US-UM": "UMI",
        "US-VI": "VIR",
    },
}


def verify_sibling_entries() -> None:
    """Fail loudly if the hardcoded list above drifts from reality, instead
    of silently reporting a unit as covered when its sibling file is gone."""
    missing = []
    for parent, units in SIBLING_COUNTRY_ENTRIES.items():
        for iso_code, sibling_alpha3 in units.items():
            if not (ROOT / f"data/countries/{sibling_alpha3}/country.yaml").exists():
                missing.append(f"{parent} {iso_code} -> {sibling_alpha3}")
    if missing:
        print("SIBLING_COUNTRY_ENTRIES lists a sibling that no longer exists:")
        for m in missing:
            print(f"  {m}")
        sys.exit(1)


def first_level_codes(alpha2: str) -> list[str]:
    """ISO 3166-2 subdivisions with no parent -- the country's top tier.

    pycountry exposes nested subdivisions (GB's 200-odd councils, FR's
    departments) alongside top-level ones; parent_code is what separates
    them. Counting all of them would make every large country look far
    worse than it is and make the number meaningless as a target.
    """
    subs = pycountry.subdivisions.get(country_code=alpha2) or []
    return sorted(s.code for s in subs if s.parent_code is None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alpha3", nargs="*", help="limit to these alpha-3 codes")
    parser.add_argument(
        "--undeclared-only",
        action="store_true",
        help="only countries whose declared total disagrees with ISO, or is missing",
    )
    args = parser.parse_args()
    verify_sibling_entries()

    rows = []
    for path in sorted(glob.glob(str(ROOT / "data/countries/*/country.yaml"))):
        with open(path) as f:
            data = yaml.safe_load(f)
        if not data.get("hasSubdivisions"):
            continue
        alpha3 = data["alpha3"]
        if args.alpha3 and alpha3 not in args.alpha3:
            continue

        iso_codes = first_level_codes(data["alpha2"])
        curated = [e["code"] for e in data.get("distinct-regions", []) if e.get("code") != "WHOLE"]
        # A curated region may span several units (NGA's NG-N covers eleven
        # states), so count the units actually claimed, not the files.
        claimed: set[str] = set()
        for entry in data.get("distinct-regions", []):
            if entry.get("code") == "WHOLE":
                continue
            claimed.update(entry.get("adminUnitCodes") or [entry["code"]])

        all_valid = {
            s.code for s in (pycountry.subdivisions.get(country_code=data["alpha2"]) or [])
        }
        unknown = sorted(c for c in claimed if c not in all_valid)
        sibling_covered = sorted(SIBLING_COUNTRY_ENTRIES.get(alpha3, {}).keys())

        coverage = data.get("regionCoverage") or {}
        declared = coverage.get("totalUnits")
        tier = coverage.get("tier", "first-level")
        # Compare like with like: a country curated at second level (UGA's
        # districts) must be measured against that tier's count, not against
        # its handful of broad first-level statistical regions.
        tier_codes = iso_codes if tier == "first-level" else sorted(all_valid - set(iso_codes))
        mismatch = declared is None or (tier_codes and declared != len(tier_codes))
        if args.undeclared_only and not mismatch:
            continue

        # "Covered" = curated directly, or covered by a sibling country
        # entry (DESIGN.md's exception) -- either way it is not a gap.
        covered = (claimed | set(sibling_covered)) & set(tier_codes)
        rows.append(
            {
                "alpha3": alpha3,
                "iso_total": len(tier_codes),
                "tier": tier,
                "files": len(curated),
                "units_claimed": len(covered),
                "sibling_covered": [c for c in sibling_covered if c in tier_codes],
                "declared": declared,
                "status": coverage.get("status"),
                "mismatch": mismatch,
                "uncovered": [c for c in tier_codes if c not in covered],
                "unknown": unknown,
            }
        )

    rows.sort(key=lambda r: (-(r["iso_total"] - r["units_claimed"]), r["alpha3"]))

    print(f"{'code':5} {'files':>5} {'units':>6} {'ISO':>5} {'decl':>5}  tier / status")
    for r in rows:
        flag = " <- declared total disagrees with ISO" if r["mismatch"] else ""
        print(
            f"{r['alpha3']:5} {r['files']:5} {r['units_claimed']:6} {r['iso_total']:5} "
            f"{str(r['declared'] or '-'):>5}  {r['tier']} / {r['status'] or '-'}{flag}"
        )

    if args.alpha3:
        for r in rows:
            print(f"\n{r['alpha3']} uncovered first-level units ({len(r['uncovered'])}):")
            print("  " + ", ".join(r["uncovered"]) if r["uncovered"] else "  (none)")
            if r["sibling_covered"]:
                siblings = SIBLING_COUNTRY_ENTRIES[r["alpha3"]]
                print(
                    f"  ({len(r['sibling_covered'])} more covered by a sibling country "
                    f"entry, not a gap: "
                    + ", ".join(f"{c} (see {siblings[c]})" for c in r["sibling_covered"])
                    + ")"
                )

    flagged = [r for r in rows if r["unknown"]]
    if flagged:
        print(
            "\nCodes not found in this machine's ISO 3166-2 data — investigate each,\n"
            "do NOT bulk-fix: the data can be wrong, and so can the ISO snapshot.\n"
            "Norway is the worked example in both directions — NOR's NO-56 (Finnmark)\n"
            "is correct and current, reinstated 2024-01-01 when Troms og Finnmark was\n"
            "split back up, while pycountry still carried the 2020-2023 merged county.\n"
            "A code flagged here is a question, not a verdict (AUDITING.md's rule on\n"
            "automated sources being wrong applies to this script too)."
        )
        for r in flagged:
            print(f"  {r['alpha3']}: {', '.join(r['unknown'])}")

    total_gap = sum(r["iso_total"] - r["units_claimed"] for r in rows)
    print(
        f"\n{len(rows)} subdivided countries, "
        f"{sum(r['units_claimed'] for r in rows)} first-level units covered, "
        f"{total_gap} not covered."
    )
    print(
        "Coverage is not a target to maximize -- see DESIGN.md's five triggers "
        "for which of those units actually need a file."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
