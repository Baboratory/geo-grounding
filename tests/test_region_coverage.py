"""Tests for scripts/region_coverage.py's sibling-country-entry exception --
the one piece of real logic in what is otherwise a reporting script. See
DESIGN.md's coverage floor for what this exception is and why it exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import region_coverage  # noqa: E402


def test_sibling_country_entries_all_resolve_to_real_directories() -> None:
    """Every alpha-3 in SIBLING_COUNTRY_ENTRIES must be a real, existing
    data/countries/<ALPHA3>/ entry -- verify_sibling_entries() is what
    catches this drifting silently, so exercise it directly rather than
    only via the CLI's sys.exit(1) path."""
    import yaml

    for parent, units in region_coverage.SIBLING_COUNTRY_ENTRIES.items():
        parent_path = ROOT / f"data/countries/{parent}/country.yaml"
        assert parent_path.exists(), parent
        alpha2 = yaml.safe_load(parent_path.read_text())["alpha2"]
        for iso_code, sibling in units.items():
            assert iso_code.startswith(f"{alpha2}-"), f"{iso_code} isn't a {parent} subdivision"
            sibling_path = ROOT / f"data/countries/{sibling}/country.yaml"
            assert sibling_path.exists(), f"{parent} {iso_code} -> {sibling}: no such entry"


def test_verify_sibling_entries_does_not_exit_on_the_real_list(
    capsys,
) -> None:
    """The real, current list should never trip the failure path -- if this
    test fails, either a sibling country file was removed/renamed and the
    list needs updating, or the list itself has a typo."""
    region_coverage.verify_sibling_entries()  # would sys.exit(1) on drift
    assert "no longer exists" not in capsys.readouterr().out
