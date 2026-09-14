# GeoGrounding

![License: MIT](https://img.shields.io/badge/code%20license-MIT-yellow.svg)
![Data: CC BY 4.0](https://img.shields.io/badge/data%20license-CC%20BY%204.0-blue.svg)

**GeoGrounding is a structured geographic and cultural context layer for AI-powered applications.**

It provides machine-readable context about a user's location and the linguistic, cultural, and commercial environment associated with it.

The goal is not to build a database about countries. GeoGrounding provides context that AI can use to understand **how a user's geographic context may affect their digital experience**.

This context can be used to adapt:

* language and communication style
* UI and content presentation
* visual and cultural elements
* sales and marketing communication
* payment and purchasing experiences
* seasonal and regional content

For example, an AI-powered application can use GeoGrounding to generate different UI, copy, calls to action, or promotional content for users in different geographic and cultural contexts.

This makes GeoGrounding particularly relevant to **AI-powered personalization and e-commerce**, where geographically adapted experiences can be evaluated through experiments such as A/B testing.

## Example

A typical flow can look like:

```text
User location
      ↓
GeoGrounding
      ↓
Geographic & cultural context
      ↓
AI
      ↓
Personalized UI / content / communication
      ↓
User experience
      ↓
A/B testing & business metrics
```

## What GeoGrounding is not

GeoGrounding is not a general-purpose knowledge source. It does not replace RAG, general-purpose knowledge bases, or geographic databases. Its purpose is narrower:

> **Provide the geographic and cultural context an AI system can use to adapt a digital experience to the user.**

## Part of Baboratory

GeoGrounding is a project of [Baboratory](https://baboratory.com/) — a creative laboratory for experimenting with AI, automation, software, and unconventional ideas. We release what we build publicly, failures included.

The project is developed as both reusable infrastructure and an experimental foundation for exploring whether geographic and cultural context can measurably improve AI-driven digital experiences.

## GeoGrounding, technically

Under the hood, this context is implemented as a structured, source-cited dataset (JSON Schema + YAML) covering countries and their regions. Every statistical claim is tied to an authoritative source, giving an AI an auditable, checkable basis instead of hallucinating. See `usage_examples/` for one reference way to consume it (IP → region → season/content selection) — the data itself isn't tied to any one integration or use case.

This project leans heavily on AI. Schema design, sourcing research, data curation, and even parts of this documentation were developed with AI doing much of the heavy lifting, while humans direct the process, review the results, and make the final decisions.

The goal is not to claim that AI-generated data is automatically correct. Instead, the project is designed to make the data auditable and checkable: statistical claims are linked to sources, deliberate gaps are documented, and `scripts/validate.py` mechanically checks structural and cross-file rules.

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

`scripts/` is this dataset's own QA tooling — it validates the data, nothing more. `usage_examples/` are reference implementations showing *how the logic should work* (IP → region → current season/content), meant to be read, used directly if your stack is Python, or ported to whatever language you're actually working in — the logic is small, ~150 lines.

Naming convention (why `validate.py` but `distinct-regions/`): see [CONTRIBUTING.md](CONTRIBUTING.md#naming-conventions).

## Design principles

The short version — see [DESIGN.md](DESIGN.md) for the full rationale and edge cases behind each of these:

- **Full ISO 3166-1 coverage (249 entries)**, dependent territories included as their own entries (e.g. `PYF` separate from `FRA`).
- **`governanceType` drives region-splitting**: `federal`/`unitary-large` countries get real, curated distinct regions (ISO 3166-2 codes); `unitary-small`/`dependent-territory` get a single synthetic `WHOLE` region.
- **Every country always has a `WHOLE` fallback region**, even ones with curated distinct regions — so a consumer never needs "does this country have distinct regions?" branching logic, and an uncurated subdivision never gets silently mapped to the wrong curated one.
- **IP→region resolution and season-calendar lookups never guess** — an unrecognized location or a missing season calendar raises a typed error (`UnknownLocationError`/`NoSeasonCalendarError`) rather than returning a plausible-looking wrong answer.
- **Every statistical claim needs an authoritative `sourceId`**; a field left out for lack of one gets a YAML comment explaining why, so "no source exists" reads differently from "not curated yet."

## Example entries

- `LTU` — a small sovereign country; no distinct regions curated. Lithuania has well-known historical/ethnographic regions, but the goal here is the opposite of cataloging heritage — a region only gets curated when it genuinely diverges *today* in something a consumer would act on, and this dataset would rather under-split than draw a distinction that doesn't actually change anything.
- `PYF` — a dependent territory (of France); no distinct regions curated, but with its own flag/languages/time zones.
- `FRA` — a large unitary country with real, present-day-distinct cultural regions (currently only 2 of ~18 distinct regions curated as an example: Brittany `FR-BRE`, Provence-Alpes-Côte d'Azur `FR-PAC`).
- `CHE` — a federal country with 4 co-official national languages (German, French, Italian, Romansh — all `domain: official` at `1.0`, per this dataset's "official is a legal-status flag, not split across co-official languages" rule); currently 4 of 26 cantons curated (`CH-ZH`, `CH-GE`, `CH-TI`, `CH-GR`), covering all 4 language regions (`CH-GR`, Graubünden, is Switzerland's only trilingual canton and the Romansh one). Also the first example where `legalConstraints`/`paymentCulture` stay country-level while `businessRhythm` genuinely differs canton by canton — Switzerland regulates shop-opening hours at the cantonal, not federal, level, so each canton cites its own law (or, for `CH-GR`, its own municipality-by-municipality pattern) for a concretely different answer to "can this shop open on Sunday?".

## Data sources

- **Base info** (flag, languages, time zones, borders): [restcountries.com](https://restcountries.com) / `mledoze/countries` (GitHub).
- **Ethnic minorities, religion %**: CIA World Factbook (there are JSON mirrors on GitHub, e.g. `factbook.json`).
- **Region-level data** (culture, cuisine, clothing): Wikidata (SPARQL), Wikivoyage — there's no structured open dataset for these categories, will need manual/LLM-assisted curation.
- **Climate**: Köppen-Geiger classification + Natural Earth admin1 boundaries.
- **Notable sights**: UNESCO World Heritage List (has an API).

## Usage — dependencies scale with what you're trying to do

An important distinction: the **lint/format chain** (`black`, `ruff`, `mypy`, `codespell`, `yamllint`, `pre-commit`) is only needed **when proposing a code change back to the project** (a PR). The **functional scripts** (`validate.py`, `get_data_by_ip.py`) are a different thing entirely: anyone can run them for their own purposes, regardless of whether they intend to contribute anything back. Each has its own small, separate dependency set:

1. **Just want the data (any language)** — no dependencies, no cloning. `data/*.yaml` reads with any YAML parser, fetched directly from GitHub:
   ```
   https://raw.githubusercontent.com/Baboratory/geo-grounding/main/data/countries/FRA/country.yaml
   ```
   See [VERSIONING.md](VERSIONING.md) for pinning a specific version instead of always getting `main`'s latest.
2. **Want to run `usage_examples/python/get_data_by_ip.py` yourself** — one dependency: `pip install pyyaml`.
3. **Want to run `scripts/validate.py` yourself** (e.g. to check the data before using it, without necessarily intending to contribute) — `pip install pyyaml "jsonschema[format]"` (the `[format]` extra is what actually makes `uri`/`date` format checks in the schemas run, instead of silently passing).
4. **Want to propose a code/data change back to the project** — only then is the full lint/format chain needed: see [CONTRIBUTING.md](CONTRIBUTING.md) (`pip install -e ".[dev]"`).

```
# case 2
pip install pyyaml
python3 usage_examples/python/get_data_by_ip.py FR BRE --date 2026-07-15

# case 3
pip install pyyaml "jsonschema[format]"
python3 scripts/validate.py

# case 4 — see CONTRIBUTING.md
pip install -e ".[dev]"
```
