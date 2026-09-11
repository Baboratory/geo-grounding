# GeoGrounding

![License: MIT](https://img.shields.io/badge/code%20license-MIT-yellow.svg)
![Data: CC BY 4.0](https://img.shields.io/badge/data%20license-CC%20BY%204.0-blue.svg)

A structured dataset of cultural and statistical data about countries and their regions (JSON Schema + YAML), designed to be used as **grounding** context for AI/LLM applications — every statistical claim is tied to an official source, so an AI has a reliable, checkable basis instead of hallucinating. Built and maintained by [baboratory.com](https://baboratory.com); see `usage_examples/` for one reference way to consume it (IP → region + season/content selection) — the data structure itself isn't tied to any one integration, it's meant for any AI/LLM context that needs reliable geographic/cultural facts.

See [LICENSE](LICENSE) (code, MIT) and [LICENSE-DATA.md](LICENSE-DATA.md) (data, CC BY 4.0). To contribute — [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). For the full design rationale — [DESIGN.md](DESIGN.md). For what a version number means and how to pin to one — [VERSIONING.md](VERSIONING.md).

## Structure

```
schema/
  country.schema.json    # country-level fields
  region.schema.json     # region-level fields
  language.schema.json   # global per-language reference (not country-specific)
data/
  countries/
    <ALPHA3>/
      country.yaml
      distinct-regions/
        <region-code>.yaml   # always at least one file; not a full list of the country's regions, only the curated ones
  languages/
    <ISO639-3>.yaml       # name + basic phrases, once per language
scripts/
  validate.py                         # checks every YAML file against the schemas + cross-file references
usage_examples/
  python/
    get_data_by_ip.py       # reference implementation: IP -> region + season/content selection
```

`scripts/` is the project's actual tooling (data QA, build-time artifact generation) — it works regardless of what language baboratory.com's own backend is written in. `usage_examples/` are reference implementations showing *how the logic should work*, meant either to be used directly (if the backend is Python) or ported to whatever language the site's backend actually is (the logic is small, ~150 lines).

**Directory/file naming convention — hyphen (`-`) or underscore (`_`)?**
- **`.py` files and any directory that is (or could become) a Python package** — always `snake_case` (`_`): `validate.py`, `get_data_by_ip.py`, `usage_examples/python/`. This isn't a style preference, it's a PEP 8 requirement — hyphens don't work in Python `import` statements (`import my-module` is a syntax error).
- **Data/output/documentation directories** (not Python packages) — `kebab-case` (`-`): `distinct-regions/`. Python has no opinion here (they're never imported), and hyphens are common and readable across most ecosystems.

## Design principles

The short version — see [DESIGN.md](DESIGN.md) for the full rationale and edge cases behind each of these:

- **Full ISO 3166-1 coverage (249 entries)**, dependent territories included as their own entries (e.g. `PYF` separate from `FRA`).
- **`governanceType` drives region-splitting**: `federal`/`unitary-large` countries get real ISO 3166-2 regions; `unitary-small`/`dependent-territory` get a single synthetic region.
- **Every country always has a `WHOLE` fallback region**, even ones with real curated regions — so a consumer never needs "does this country have regions?" branching logic, and an uncurated subdivision never gets silently mapped to the wrong curated one.
- **IP→region resolution and season-calendar lookups never guess** — an unrecognized location or a missing season calendar raises a typed error (`UnknownLocationError`/`NoSeasonCalendarError`) rather than returning a plausible-looking wrong answer.
- **Every statistical claim needs an official `sourceId`**; a field left out for lack of one gets a YAML comment explaining why, so "no source exists" reads differently from "not curated yet."

## Example entries

- `LTU` — a small sovereign country, no regions.
- `PYF` — a dependent territory (of France), no regions, but with its own flag/languages/time zones.
- `FRA` — a large unitary country with real cultural regions (currently only 2 of ~18 regions filled in as an example: Brittany `FR-BRE`, Provence-Alpes-Côte d'Azur `FR-PAC`).
- `CHE` — a federal country with 4 co-official national languages (German, French, Italian, Romansh — all `domain: official` at `1.0`, per this dataset's "official is a legal-status flag, not split across co-official languages" rule); currently 3 of 26 cantons filled in (`CH-ZH`, `CH-GE`, `CH-TI`), chosen to cover 3 of the 4 language regions. Also the first example where `legalConstraints`/`paymentCulture` stay country-level while `businessRhythm` genuinely differs canton by canton — Switzerland regulates shop-opening hours at the cantonal, not federal, level, so `CH-ZH`/`CH-GE`/`CH-TI` each cite their own cantonal law for a concretely different answer to "can this shop open on Sunday?".

## Data sources

- **Base info** (flag, languages, time zones, borders): [restcountries.com](https://restcountries.com) / `mledoze/countries` (GitHub).
- **Ethnic minorities, religion %**: CIA World Factbook (there are JSON mirrors on GitHub, e.g. `factbook.json`).
- **Region-level data** (culture, cuisine, clothing): Wikidata (SPARQL), Wikivoyage — there's no structured open dataset for these categories, will need manual/LLM-assisted curation.
- **Climate**: Köppen-Geiger classification + Natural Earth admin1 boundaries.
- **Notable sights**: UNESCO World Heritage List (has an API).

## Usage — dependencies scale with what you're trying to do

An important distinction: the **lint/format chain** (`black`, `ruff`, `mypy`, `codespell`, `yamllint`, `pre-commit`) is only needed **when proposing a code change back to the project** (a PR). The **functional scripts** (`validate.py`, `get_data_by_ip.py`) are a different thing entirely: anyone can run them for their own purposes, regardless of whether they intend to contribute anything back. Each has its own small, separate dependency set:

1. **Just want the data (any language)** — no dependencies. `data/*.yaml` reads with any YAML parser. Fetching directly without cloning (e.g. via raw.githubusercontent.com) works too, once this is pushed to a real GitHub remote.
2. **Want to run `usage_examples/python/get_data_by_ip.py` yourself** — one dependency: `pip install pyyaml`.
3. **Want to run `scripts/validate.py` yourself** (e.g. to check the data before using it, without necessarily intending to contribute) — `pip install pyyaml jsonschema`.
4. **Want to propose a code/data change back to the project** — only then is the full lint/format chain needed: see [CONTRIBUTING.md](CONTRIBUTING.md) (`pip install -e ".[dev]"`).

```
# case 2
pip install pyyaml
python3 usage_examples/python/get_data_by_ip.py FR BRE --date 2026-07-15

# case 3
pip install pyyaml jsonschema
python3 scripts/validate.py

# case 4 — see CONTRIBUTING.md
pip install -e ".[dev]"
```
