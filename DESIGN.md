# Design rationale

The deep-dive companion to [README.md](README.md): why the schema and tooling work the way they do, the edge cases that shaped each decision, and the cross-file rules `scripts/validate.py` enforces that JSON Schema alone can't express. README.md covers *what's here and how to use it*; this file covers *why it's built this way* — useful when you're adding a country/region yourself, extending the schema, or want to understand a design decision well enough to reuse or challenge it (including as context for an AI agent working on this dataset).

## If documents disagree, who's authoritative?

Wording drifts out of sync sometimes; when it does, this is the order to trust, most authoritative first:

1. `schema/*.schema.json` — the structural contract. If data validates against it, the shape is correct, full stop.
2. `scripts/validate.py` — the cross-file/semantic rules a JSON Schema can't express (source-reference resolution, the `WHOLE` invariant, season-calendar coverage, the `governanceType` invariant, etc.).
3. This file — the intended data model and the reasoning behind it, including cases the schema/validator can't enforce.
4. `CONTRIBUTING.md` — the contributor workflow built on top of 1-3.
5. `README.md` — a user-facing summary; if it ever describes the model differently from this file, this file wins.
6. `llms.txt` — pure navigation for an AI agent orienting itself, not an independent source of rules.

Not worth repeating this list elsewhere — one clear place beats a stale copy in five files.

## Core design decisions

**Country list — full ISO 3166-1 (249 entries), not just the 195 sovereign states.**
Dependent territories (French Polynesia `PYF`, Puerto Rico `PRI`, Greenland `GRL`, etc.) get their own alpha-3/alpha-2 code and flag, distinct from their parent state — matching how a "pick your country" menu should actually work (see the `PYF` example — separate from `FRA`, even though it's politically part of France).

**Region-splitting rule (the `governanceType` field):**
| governanceType | Regions | Example |
|---|---|---|
| `federal` | Mandatory, by state/land/province (real ISO 3166-2) | US, Germany, Switzerland, Canada, Brazil, India, Australia |
| `unitary-large` | Cultural regions (real ISO 3166-2) | France, Italy, Poland, Spain, Japan, China, UK, Ukraine |
| `unitary-small` | None — a single synthetic region | Lithuania, Estonia, Georgia, Uruguay |
| `dependent-territory` | None — a single synthetic region | all 54 non-sovereign ISO 3166-1 entries (no exceptions) |

A country is classified "unitary-large" when it meets at least 2 of 3 criteria: population >20-25M, officially recognized regional/minority languages, or a widely recognized cultural-historical regional identity.

This is a real invariant, not just a convention some countries happen to follow: `federal`/`unitary-large` always means `hasSubdivisions: true` and `iso3166_2_prefix` equal to `alpha2`; `unitary-small`/`dependent-territory` always means `hasSubdivisions: false` and `iso3166_2_prefix: null`. `scripts/validate.py` checks all four fields agree with each other on every country file.

**Every country always has a `distinct-regions[]` array with exactly one `code: WHOLE` entry** — even countries with real, curated regions (e.g. `FRA` has `FR-BRE`, `FR-PAC` **and** `WHOLE`). The `WHOLE` file holds generic, national/symbolic-level content (not tied to a specific region) and is used as the fallback when the admin unit found by IP geolocation isn't one of the curated ones (e.g. a visitor from Île-de-France, before an `FR-IDF` file exists) — so the site always has something to show, instead of misassigning the visitor to an arbitrary curated region. This way every region-level field (climate, landmarks, cuisine, sports, religion, clothing, entertainment) is always read from the same path — the consumer (the site) never needs separate logic for "does this country have regions or not." The name `distinct-regions` (rather than just `regions`) deliberately emphasizes that this is **not** a complete list of the country's administrative units, only the curated, documented ones — e.g. `FRA` currently has 2 of ~18 real French regions filled in (plus `WHOLE`).

**`iso3166_2_prefix`** — equal to `alpha2` when `hasSubdivisions: true` (because ISO 3166-2 subdivision codes are built from alpha-2, not alpha-3, e.g. `FR-BRE`, not `FRA-BRE`), otherwise `null`.

**`climates[]`** — a deliberately free-form list of Köppen codes with a description (`{koppenCode, description}`), not tied to specific months/seasons. That's enough for a general picture of the region (several climate zones can occur in one region, e.g. `FR-PAC` has both Mediterranean and Alpine climate). If a more precise link is needed in the future (e.g. "what's the climate in this specific month"), that will be a separate, stricter field — the current one is left as-is so it doesn't complicate the simple case.

## IP geolocation mapping (`adminUnitCodes`)

Every `distinct-regions[]` entry in `country.yaml` (when `hasSubdivisions: true`) has `adminUnitCodes[]` — a list of ISO 3166-2 codes that the IP geolocation result is matched against to find our curated region. This will usually be the same as the `code` value, but allows multiple codes if the curated region spans more than one official administrative unit.

Practical flow: IP → geolocation DB returns `{countryCode, subdivisionCode}` → `resolve_region(countryCode, subdivisionCode)` (see `usage_examples/python/get_data_by_ip.py`) finds the matching `distinct-region` file. Three possible outcomes (the `matchedBy` field):
- `"adminUnitCode"` — an exact match with a curated region (e.g. `FR` + `BRE` → Brittany).
- `"whole-country"` — a country with no real regions (`hasSubdivisions: false`); `WHOLE` is the only/primary content.
- `"whole-country-fallback"` — the country has real regions, but this specific admin unit isn't documented yet (e.g. Île-de-France, before an `FR-IDF` file exists) — the resolver **does not** return an arbitrary curated region (that would be wrong, e.g. showing Brittany content to a Paris visitor), it uses the generic `WHOLE` file instead. The site may (but doesn't have to) flag this case specifically in the UI (e.g. "showing general France info").

### Supported GeoIP sources

The project is set up to work with geolocation sources that (a) give region/subdivision level for free (not just country) and (b) allow commercial use without an extra paid license for a site's own internal use:

| Source | Cost | How to use | Region (ISO 3166-2)? | License |
|---|---|---|---|---|
| **MaxMind GeoLite2 City** | Free | `.mmdb` file, read locally | Yes | Requires a free account + license key; free for commercial use for a site's own internal purposes, just not for reselling/repackaging the DB itself |
| **DB-IP Lite (City)** | Free | `.mmdb`/CSV, updated monthly | Yes (lower accuracy than the paid tier) | CC BY 4.0 — commercial use allowed, attribution required |
| **IP2Location LITE (DB3)** | Free | CSV/BIN, local | Yes (DB3 = IP-COUNTRY-REGION-CITY) | Its own LITE license, commercial use allowed |

Deliberately **not included**: `ip-api.com` (free tier is non-commercial use only) and `ipinfo.io` Lite (free, but country-level only — region requires the paid Core plan).

### Fallback when detection fails

`resolve_region()` **never guesses a default country/region** — if it doesn't get a country code at all (GeoIP failed: private/bogon IP, VPN, DB miss) or the code given isn't one of the 249 ISO 3166-1 entries in this dataset, it raises `UnknownLocationError` (a `LookupError` subclass). This is a **deliberate, expected** signal, not a bug — deciding what to show in that case (generic/international content, a default language, etc.) is up to the calling application, not this library.

Recommended layered strategy before hitting `UnknownLocationError`:
1. The primary region/city-level GeoIP DB (one of the three above).
2. If that DB doesn't find the IP, or only returns a country with no region — try the **`GeoLite2-Country`** (not City) database: since it needs less precision, its IP block coverage is broader than the City version. If you're behind Cloudflare, their `CF-IPCountry` HTTP header is an even simpler, zero-dependency option for the same purpose.
3. If even that fails — `resolve_region()` raises `UnknownLocationError`, and the site decides for itself.

All three supported sources return a subdivision code, either directly or easily converted to the full ISO 3166-2 format (`{alpha2}-{subdivisionCode}`) — exactly what's needed for `adminUnitCodes` matching. MaxMind and DB-IP both use the `.mmdb` format (different content schemas though: MaxMind needs the `geoip2` library, DB-IP needs a more generic `.mmdb` reader, e.g. Python's `maxminddb`, not `geoip2`); IP2Location uses its own CSV/BIN format with its own reader library (an `IP2Location` package for the relevant language). `usage_examples/python/get_data_by_ip.py` currently accepts an already-parsed `{countryCode, subdivisionCode}` pair — the actual DB-reading layer (MaxMind/DB-IP/IP2Location specific) isn't wired in yet; we'll add it once you decide which of the three to use first.

## Determining the current season (`seasonCalendar`)

**Seasonal fields** (`entertainment`, `traditionalDishes`, `traditionalClothing`) — `season` is a closed `enum`: `spring` / `summer` / `autumn` / `winter` / `dry` / `wet` / `allYear`. Not just the four seasons, because tropical/equatorial regions (e.g. French Polynesia) split by `dry`/`wet`, while temperate regions split by `spring`/`summer`/`autumn`/`winter`; regions without meaningful seasonality get a single `allYear` entry.

Every region file that uses at least one non-`allYear` season also has `seasonCalendar[]` — a map from each season label to the calendar months (1-12) it covers **specifically in that region**. This makes "what season is it right now?" and "what should we show right now?" directly answerable from the data — see `usage_examples/python/get_data_by_ip.py` (the `current_season()`/`current_content()` functions, or `get_data_by_ip()`, which combines the IP→region lookup and season determination into one call):

```
python3 usage_examples/python/get_data_by_ip.py PF --date 2026-01-15
# {"country": "PYF", "regionCode": "WHOLE", "matchedBy": "whole-country", "season": "wet",
#  "content": {"entertainment": ["Indoor va'a training season"], "traditionalDishes": [...], "traditionalClothing": [...]}}
```

Months are given directly (rather than via a hemisphere flag + a general rule), because that's the only way to correctly handle both the hemisphere flip (French Polynesia's "dry" season runs May-October, which calendar-wise coincides with the Northern Hemisphere's summer/autumn — verified via Tahiti Tourisme) and tropical dry/wet seasons, which don't follow any simple hemisphere rule at all. `scripts/validate.py` checks that a region's `seasonCalendar` months form a complete, non-overlapping partition of the 12 months, and that every season actually used has a calendar entry.

**Same "never guess" rule as `resolve_region()`**: if a region has no `seasonCalendar` (because all its seasonal values are `allYear`, or the calendar just hasn't been filled in yet), `current_season()` raises `NoSeasonCalendarError` rather than guessing a season. `current_content()` in that case simply returns only the `allYear` content (no error) — a missing calendar doesn't mean there's nothing to show, only that there's nothing seasonal to add.

## Language modeling (`languageUsage[]`)

**Language codes — ISO 639-3** (not BCP 47), matching baboratory.com's existing convention for this data format. A country's language usage is kept as one flat `languageUsage[]` list: `(languageCode, domain, speakersShare)` rows, where `domain` is `official` / `locallySpoken` / `foreign`. The language's display name and basic phrases (`commonPhrases`) aren't repeated per country — they're kept once, globally, in `data/languages/<code>.yaml`.

**What `speakersShare` means depends on `domain`:**
- `official` — **always `1.0` for every de jure official language**, no matter how many there are (it's a legal status, not a population measure — so it's never split across multiple official languages, e.g. South Africa's 11 official languages each get `1.0`, not `1/11`). It does *not* mean actual usage — that's captured by a separate `locallySpoken` entry for the same language.
- `locallySpoken` / `foreign` — the real share of the population (0–1); entries within a domain don't need to sum to 1 (bilingualism, rounding).

E.g. `PYF`: only `fra` has `domain: official` (per Article 57 of the 2004 autonomy statute — French is the sole official language; Tahitian is legally protected as cultural heritage, but is **not** official). Actual usage is shown via separate `locallySpoken` entries for both languages.

`name.local[]` (on both `country.yaml` and a region file) follows the same "official is a legal-status flag" spirit but isn't identical to it: at country level it's one entry per `languageUsage[]` row with `domain: official`; at region level it's only the language(s) actually used/official **in that specific region**, which for a federal country's subdivisions is very often a strict subset of the country's full list (e.g. `CHE`'s German-speaking `CH-ZH` has one entry, not all four national languages) — except the `WHOLE` fallback, which gets the full country-level list since it represents the whole country generically. "Local" also isn't "official-only": `PYF` `WHOLE` has both `fra` (official) and `tah` (not official, but genuinely locally spoken). See `CONTRIBUTING.md`'s Hard rules for the enforced version of this.

**Every statistical entry must have a `sourceId` pointing to an official source.** See "Source grounding" below.

## Source grounding (`sources[]` / `sourceId`)

All statistical fields (`ethnicGroups[].percent`, `languageUsage[].speakersShare`, `religions[].percent`) must have a `sourceId` pointing to an entry in that same file's `sources[]` list — the schema requires this (`required`), and `scripts/validate.py` additionally checks that every `sourceId` used actually exists in that file's declared `sources[]` (a cross-reference, similar to `languageCode` → `data/languages/*.yaml`).

Every `sources[]` entry has: `id`, `name` (the specific document/table's title), `publisher` (the official body), `url`, optional `year`/`accessedDate`, and a **required `note`** — stating precisely *what* was taken from this source (e.g. "ethnicGroups percentages; lit locallySpoken share").

**When no official source exists, the field is left out, not guessed.** Checking the example data turned up a few such cases:
- **France (`FRA`) has no `ethnicGroups` or region-level `religions` fields** — a 1978 law and the Constitutional Council prohibit the state from collecting ethnicity/religion statistics (the INSEE census doesn't ask these questions). The reason is written as a YAML comment in the file.
- **French Polynesia (`PYF`) has no `ethnicGroups` or `religions`** — ISPF doesn't publicly publish exact percentages (ethnic composition), and the last census to record religion was in 1971; the ~38%/38% figures circulating online trace back to a researcher interview, not official statistics.
- These gaps are marked with YAML comments right where the field would be expected — so it's clear it's a deliberate omission, not an oversight.

Checking the data also turned up a real error: an earlier version of `PYF` had `tah` marked as `domain: official`, when under Article 57 of the 2004 autonomy statute only French is official — this has been fixed.

### Rule: every deliberately omitted field gets a comment

Every `region.schema.json` field beyond `code`/`name` (as well as `country.schema.json`'s `ethnicGroups`) is **optional** — a deliberate design choice, not sloppiness: not every country/region has a distinctive traditional costume, a unique animal species, or officially recorded religion/ethnicity statistics (see the `FRA`/`PYF` examples above). The schema allows this without errors — the field is simply not written.

**But every case where a field is deliberately left out (not just "haven't gotten to it yet") needs a YAML comment above that spot, explaining why** — see the pattern in `FRA/country.yaml`, `FRA/distinct-regions/*.yaml`, `PYF/country.yaml`, `PYF/distinct-regions/whole.yaml`. This distinguishes "the data doesn't and can't exist" from "the data just hasn't been collected yet" — the latter needs no comment, the field will simply be filled in later.
