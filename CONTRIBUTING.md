# Contributing

## Setup

```
pip install -e ".[dev]"
pre-commit install     # do this once per clone -- without it, nothing below runs automatically
python3 scripts/validate.py
```

**Every applicable check must pass before a change is committed** —
`black`, `ruff`, `mypy`, `codespell`, and `yamllint` run on every commit;
`scripts/validate.py` runs too, but only when a commit actually touches
`data/` or `schema/` (see `.pre-commit-config.yaml`'s `files:` scoping —
no point re-validating the dataset for a docs-only change).
`pre-commit install` makes this automatic on every `git commit`, but that's
a per-clone opt-in, not something that follows the repo itself — a fresh
clone runs nothing until someone runs that command, so don't treat
"I forgot to run pre-commit install" as an excuse — run
`pre-commit run --all-files` by hand if you're not sure it's wired up.

A GitHub Actions workflow (`.github/workflows/validate.yml`) runs the same
checks on every push and PR, so a forgotten local install still gets
caught — but that's a safety net, not a substitute for running it
yourself and seeing the result before you push.

`scripts/validate.py` specifically checks JSON Schema conformance plus a
set of cross-file rules JSON Schema alone can't express (see the rules
below — each one is enforced there).

## Adding or editing a country

1. Decide `governanceType` first (`federal` / `unitary-large` / `unitary-small`
   / `dependent-territory`) — see DESIGN.md's "Core design decisions" for the
   criteria. This decides whether you need real regions or just `WHOLE`.
2. Create `data/countries/<ALPHA3>/country.yaml` against `schema/country.schema.json`.
   Every `languageUsage[].languageCode` you use needs a matching
   `data/languages/<code>.yaml` — check it already exists before writing it;
   if not, create it (`code`, `name.eng`, `name.local`, optionally
   `commonPhrases`), same as `deu`/`ita`/`roh` were added alongside `CHE`.
   `scripts/validate.py` fails loudly if you miss one, but don't rely on
   that catching it — it's easy to write the whole country file, hit
   validate, and only then realize three language files are missing.
3. Create `data/countries/<ALPHA3>/distinct-regions/whole.yaml` — **every**
   country needs exactly one `code: WHOLE` entry, even ones with real
   regions (it's the fallback content when a visitor's specific subdivision
   isn't curated yet — see DESIGN.md's "IP geolocation mapping").
4. If `hasSubdivisions: true`, add real ISO 3166-2 region files too, each
   referenced in `country.yaml`'s `distinct-regions[]` with matching
   `adminUnitCodes[]`.
5. Run `python3 scripts/validate.py` and fix everything it flags.

## Hard rules (enforced by `scripts/validate.py`)

- **Every statistic needs a source.** `ethnicGroups[].percent`,
  `languageUsage[].speakersShare`, `religions[].percent`,
  `legalConstraints[]`, `paymentMethodShares[].percent`, and
  `businessRhythm.notableShutdownPeriods[]` (when sourced) each require a
  `sourceId` pointing to an entry in that file's own `sources[]`. Each
  source needs `id`, `name`, `publisher`, `url`, and a `note` saying
  *exactly* what was taken from it, and `sources[].id` must be unique
  within the file — a duplicate would make `sourceId` references
  ambiguous. No authoritative source, no field — see the next rule.
  Primary official sources (a national statistics office, a government
  ministry, a central bank, the legal text itself) are preferred, but a
  reliable academic, institutional, or secondary source is fine when it's
  genuinely the best one available, as long as `source.note` says so
  plainly (see `CHE`'s payment-method-share source, a university payment
  study, because no equivalent central-bank breakdown was found).
  `paymentCulture` and `communicationStyle` are the deliberate exception —
  they're modeled as qualitative/customary, not statistical, so no
  `sourceId` is required (cite one informally in prose if you have a good
  one, but don't force a field to exist just to satisfy this rule).
  `businessRhythm.sourceIds[]` is similar but narrower: most
  `businessRhythm` content is customary description and doesn't need one,
  but when a region's law genuinely differs from the rest of the country
  (a federal country's canton/state having its own trading-hours law, say)
  and `notes`/`restDays`/etc. state that as a specific legal fact, cite it
  there — see `CHE`'s `CH-ZH`/`CH-GE`/`CH-TI` for the pattern.
- **Write `note` (and YAML comments) in plain language, not schema jargon.**
  A `note` should read clearly to someone who has never seen this schema —
  don't write "paymentMethodShares — card payments as 56%...", write "the
  share of non-cash payments made by card (56%)". This applies to field
  names generally (`ethnicGroups`, `legalConstraints`, `businessRhythm`,
  ...) but especially to `domain` (`official`/`locallySpoken`/`foreign`) —
  compounds like "foreign-domain shares" or "official-domain status" read
  as made-up terminology to a reader who doesn't already know that field.
  Say what it actually means instead: "the share who speak it as a foreign
  language", "the country's sole official language".
- **A field you deliberately leave out needs a comment saying why.**
  Not every field applies to every place (not every country has an official
  religion census, not every region has a distinct traditional costume).
  Schema makes almost everything optional for exactly this reason. But
  "deliberately omitted, no source exists" and "just haven't gotten to it
  yet" look identical without a comment — see `data/countries/FRA/country.yaml`
  or `data/countries/PYF/distinct-regions/whole.yaml` for the pattern.
- **`official`-domain `speakersShare` is always `1.0`**, never split across
  co-official languages — it's a legal-status flag, not a population
  measurement. Real usage goes in a separate `locallySpoken` row for the
  same `languageCode`.
- **`name.local[]` means "locally used", and *where* it's local differs
  between `country.yaml` and a region file.** At country level, it's one
  entry per `languageUsage[]` row with `domain: official` — a country with
  4 official languages (e.g. `CHE`: deu/fra/ita/roh) gets 4 entries. At
  region level, it's only the language(s) actually used/official **in that
  specific region**, which for a federal country's subdivisions is very
  often a strict subset of the country's full list — don't just copy the
  country's official-language list onto every region. E.g. `CHE`'s
  German-speaking `CH-ZH` has one entry (`deu`), not all four, even though
  Switzerland has 4 official languages nationally; a genuinely multilingual
  region (e.g. a trilingual canton) would legitimately have more than one.
  The one region-level exception is the `WHOLE` fallback — since it
  represents the whole country generically rather than one specific region,
  it gets the full country-level list, same as `country.yaml` (see `CHE`'s
  `WHOLE` for all 4). And "local" isn't "official-only" either: `PYF`
  `WHOLE` has both `fra` (official) and `tah` (not official, but genuinely
  locally spoken) — a language only needs to be locally used, not legally
  official, to belong here.
- **Every `distinct-regions[]` entry's `code` must match the `code` field
  inside the file it points to**, and no two entries in the same
  `distinct-regions[]` may share a `code`.
- **When `hasSubdivisions: false`, `distinct-regions[]` must contain
  *exactly* `WHOLE` — nothing else.** A country with no real subdivisions
  doesn't get to also list a non-`WHOLE` region alongside it.
- **A non-`WHOLE` region's `code`, and every one of its `adminUnitCodes`,
  must start with that country's own `alpha2` prefix** (`FR-*` for `FRA`,
  never a code that belongs to a different country's ISO 3166-2
  namespace) — easy to get wrong when copying one country's region file as
  a starting point for another's. `adminUnitCodes` also can't repeat
  across two different regions in the same country: `resolve_region()`
  (see `usage_examples/python/get_data_by_ip.py`) returns whichever region
  it finds the match in first, so a duplicate would make the result depend
  on YAML ordering rather than being well-defined.
- **`seasonCalendar` months must partition the year exactly** (each of 1-12
  in exactly one season, no gaps, no overlaps) whenever a region uses any
  season other than `allYear`.
- **Language codes are ISO 639-3** (`lit`, `fra`, not `lt`, `fr`) everywhere,
  matching baboratory.com's existing convention for this data format. A
  `data/languages/<code>.yaml` file's internal `code` field must match its
  own filename — the code is both the file's identifier and its content.
- **`governanceType`/`hasSubdivisions`/`iso3166_2_prefix` must agree.**
  `federal`/`unitary-large` requires `hasSubdivisions: true` and
  `iso3166_2_prefix` equal to `alpha2`; `unitary-small`/`dependent-territory`
  requires `hasSubdivisions: false` and `iso3166_2_prefix: null`. See
  DESIGN.md's "Core design decisions" for why.

## Naming conventions

- `.py` files and any directory that is (or could become) a Python package
  → `snake_case` — this isn't a style preference, `import my-module` is a
  syntax error, so this is the one place the convention isn't optional.
- Everything else (data/output/doc directories) → `kebab-case`.

## Commit identity

Use your own name and email (normal `git config user.name`/`user.email`,
or whatever GitHub attributes your PR to) — there's no special convention
to follow here. You may notice some commits in the history authored by
Baboratory's in-universe staff characters; that's the maintainers' own
house style for their own commits, not something expected of contributors.

## Code and text quality

```
pip install -e ".[dev]"
pre-commit install    # runs everything below automatically on every commit
```

- **`black`** — Python formatting, no bikeshedding about style.
- **`ruff`** — Python linting (unused imports, obvious bugs, import order).
- **`mypy`** — type checking. Every function here has type hints; mypy
  catches the class of bug type hints are for (it once caught a function
  declared to return nothing being fed into `sys.exit()`, which happens to
  work but wasn't the intent).
- **`codespell`** — catches typos in code, comments, and docs. Configured
  (`pyproject.toml`'s `[tool.codespell]`) with an ignore-list for real
  proper nouns and non-English words it doesn't recognize (French place
  names, German legal-citation terms, etc.) rather than skipping whole
  files.
- **`yamllint`** — structural YAML style (indentation, trailing whitespace,
  duplicate keys) as a complement to `scripts/validate.py`'s schema
  checking — the two catch different things.
- **`scripts/validate.py`** — the actual data/schema rules (sourcing,
  WHOLE regions, season calendars — see above). Runs as a pre-commit hook
  too, scoped to `data/`/`schema/` changes.

**None of these detect "AI-generated code."** That's not a property a
linter can check — formatting and type-checking tools enforce
*consistency*, not authorship. What actually reads as generated (and what
these tools don't catch) is a writing-discipline problem, not a tooling
one:

- Comments explain *why*, not *what* — if removing a comment wouldn't
  confuse a future reader, it shouldn't be there. This applies to YAML
  omission-comments too: state the reason, not a restatement of the field
  name.
- No template docstrings (`Args:` / `Returns:` / `Raises:` blocks) on
  functions simple enough not to need them — a one-line summary is enough
  when the type hints already say what goes in and out.
- Don't explain something the code already makes obvious; don't hedge or
  over-qualify claims in comments or commit messages.

There's no lint rule for "sounds natural" — this is something to read for,
not something CI enforces.
