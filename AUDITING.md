# Auditing this dataset

A guide for reviewing already-merged data against this repo's own rules —
whether you're a human maintainer, an external reviewer, or an AI agent
asked to check a batch of countries for compliance. This is a different job
from [CONTRIBUTING.md](CONTRIBUTING.md) (which is about *adding* data) and
from [MAINTAINING.md](MAINTAINING.md) (which is about *releasing* it): an
audit assumes the data already validates and already shipped, and asks
"does it actually hold up against the rules it claims to follow?"

Same authority order as [DESIGN.md](DESIGN.md#if-documents-disagree-whos-authoritative):
`schema/*.schema.json` > `scripts/validate.py` > `DESIGN.md` > `CONTRIBUTING.md`
> `README.md`. If a finding can't be traced to one of those, it isn't a
rule violation — it might still be a good catch (see the severity scale
below), but don't call it a hard-rule violation unless a specific rule in
one of those four says so.

## Read this section before anything else

The single most common false positive in past audits of this dataset has
been treating a **disclosed estimate or a Wikipedia citation as an automatic
rule violation**. It isn't. `DESIGN.md`'s "Source grounding" section says so
explicitly, with named examples (`CHE`, `LTU`) of exactly this pattern being
the accepted, intended practice — not a loophole, not something that slipped
past review.

The rule that *does* exist — "when no authoritative source exists at all,
the field is left out, not guessed" — is about a **different, narrower**
situation: cases like `FRA`/`PYF`, where no source exists whatsoever (a law
prohibits collecting the statistic, or it was simply never published by
anyone). It is not about a real institution's own disclosed estimate.

| This is fine (not a violation) | This is a real problem |
|---|---|
| `note` says "estimate", "approximate", "FLAGGED", or "composite" **and names roughly where the figure comes from** (a named survey, institution, or study) | `publisher` names one body (e.g. a national statistics office) while `url` actually points somewhere else — a mismatch between what a source claims to be and what it actually is |
| A `sources[]` entry whose `url` is Wikipedia, used as a secondary rendering of a real underlying figure, disclosed as such | `publisher` is literally "Composite estimate" / "Placeholder" with **no named institution anywhere** in the entry — that's not disclosure, it's an empty citation |
| A figure sourced to a reputable secondary/academic source when no primary one is fetchable, with the note saying so | A `sourceId` whose `note`/`url` doesn't actually establish the value it's attached to (e.g. a legal-status source cited for a usage percentage, an ethnicity census cited for a language share) |
| Two different rows in the same field citing two different institutions, each disclosed accurately | A field with genuinely nothing behind it at all — not even a named secondary source — presented as if it were data |

Before writing up any finding about a source, actually open (or otherwise
verify) the `url` and compare it against what `publisher` and `note` claim.
Most real sourcing problems in this dataset have turned out to be a
mismatch between those three fields, not the mere presence of an estimate.

Two more false-positive patterns worth knowing before you start:

- **A difference between files that looks like a bug may be an established
  convention instead — grep the dataset before "fixing" it.** Example: this
  dataset uses both `ara` (the Arabic macrolanguage ISO 639-3 code) and
  `arb` (Standard Arabic) as the `languageCode` for the `official` Arabic
  entry, depending on the file — `ara` in `DZA`/`ARE`/`IRQ`/`ESH`/`IRN`/
  `MRT`, `arb` in `EGY`/`BHR`/`COM`/`DJI`/`ERI`/`JOR`/`KWT`/`LBY`/`OMN`/
  `QAT`/`SOM`/`SSD`/`TCD` and more. Neither is wrong on its own — both are
  valid ISO 639-3 codes — but the split is real and predates any single PR.
  Changing one file to "match" the other without first checking how many
  *other* files already use the pattern you're about to change risks
  breaking a working, if imperfect, convention (and, if you delete a
  `data/languages/*.yaml` file because one file's use of it looked like a
  mistake, you can break every other file that legitimately depends on it
  — always `grep -r` for a `languageCode` across `data/countries/` before
  removing its language file). Flag a real, dataset-wide inconsistency like
  this as `[hygiene]` for a future cleanup pass, not as a same-file fix.
- **An automated fetch or search summary can itself be wrong — cross-check
  before trusting it as the basis for a finding.** A `WebFetch`-style tool
  reading a poorly-rendered government legal page once reported that
  Bangladesh's constitutional Article 3 covers the state religion and
  Article 2A the state language — backwards from reality (Article 3 is
  "The state language" and Article 2A is "The state religion"; a plain web
  search of the article text confirmed this immediately). If a single
  automated read of a source produces a surprising claim — especially one
  that would mean an already-shipped file is wrong — verify it a second,
  independent way (a plain search for the specific fact, a different
  fetch of the same page) before writing it up. Don't let one unreliable
  tool call become a false "confirmed" finding.

## What to check

For each country/region file:

1. **Schema validity and cross-file invariants** — run `scripts/validate.py`
   first; anything it flags is a hard error, not a judgment call. It checks
   the `WHOLE` invariant, `governanceType`/`hasSubdivisions`/
   `iso3166_2_prefix` agreement, `sourceId` resolution, region `adminUnitCodes`
   uniqueness, `seasonCalendar` partitioning, `languageCode` → `data/
   languages/*.yaml` existence, and (since a 2026-09 remediation) that every
   `languageUsage` row with `domain: official` has `speakersShare: 1.0` — see
   `DESIGN.md` for what each one means. Don't manually re-derive this last
   one; if `validate.py` passes, it's not a finding.
2. **`governanceType` classification** — is the 2-of-3 `unitary-large` test
   (population >20-25M, recognized minority/regional languages, a widely
   recognized cultural-historical regional identity) actually argued, not
   just asserted? For `federal`, is there a genuine constitutional
   federation (real, separately-governed states/provinces), independent of
   population size (see `FSM`, a country of ~113k people that's correctly
   `federal`)? Is the split into curated regions proportionate — enough to
   reflect real, documented internal diversity, not so many that a small,
   linguistically/culturally uniform country gets split for its own sake?
   A recurring, legitimate way the "recognized minority/regional languages"
   leg gets satisfied without co-official status: a country-level law or
   body that names specific languages as "national languages", "recognized
   regional languages", or grants them standing only in specific
   districts/regions — this counts as PASS even though the country's sole
   *official* language is something else (established precedent: `NAM`'s 13
   national languages, `GUY`'s regional languages, `SSD`'s ~60
   constitutionally-named national languages, `LBY`'s 2013 Tamazight/Tuareg/
   Tebu recognition law). If a file's own comment concedes it meets only 1
   of the 3 criteria while still classified `unitary-large`/`federal`, check
   whether this pattern actually applies before treating it purely as a
   violation to downgrade — it may just be an under-argued but correct call.
3. **`name.local` completeness** — does it include *at least* one entry per
   `domain: official` language at country level (and the full list again at
   `WHOLE`), and only the languages actually used/official in a specific
   curated region there? A country with N official languages should show all
   N unless there's a documented reason not to (see `FSM`'s Yap file, which
   should list Ulithian and originally didn't). That's a floor, not a
   ceiling: an *extra* entry for a genuinely, verifiably locally-spoken
   non-official language (the `PYF` `tah`-alongside-official-`fra` pattern,
   also legitimately used for e.g. Danish in Greenland/Faroe country files)
   is not itself a defect — don't flag "this language isn't official" as a
   `name.local` finding unless the entry is also unverified/fabricated.
   `WHOLE` should mirror the country-level list exactly, including any such
   extras — a mismatch between the two (country has 9 entries, `WHOLE` has
   1) is the actual `[data]` finding, not the extras themselves.
4. **Source provenance** — for every `sourceId`, does `publisher` match what
   `url` actually is? Does the `note` say precisely what was taken from the
   source (not vaguely "background")? Is the source itself the right
   *kind* of document for the claim (a legal text doesn't establish a usage
   percentage; an ethnicity census doesn't establish a language share)?
5. **Arithmetic** — do `ethnicGroups`/`religions`/`languageUsage` rows within
   a domain sum sensibly? A gap of 1-5 points inherited from the underlying
   published breakdown (and disclosed as such) isn't a defect; an
   unexplained, uncommented gap is worth flagging as hygiene, not blocking.
6. **Internal consistency** — do the country file, its `WHOLE` file, and its
   curated region files agree with each other (a timezone claimed in one
   place and contradicted in another; a percentage in a comment that doesn't
   match the actual row; a note that says a figure supports one row when
   the row's `sourceId` actually points elsewhere)?
7. **Geographic/legal facts that are independently checkable** — flag
   emoji vs. `alpha2` (should always decode to the same two-letter code via
   regional-indicator symbols), IANA timezone validity (does the zone
   actually belong to *this* country?), and any similarly hard, checkable
   fact. These are cheap to verify and catch real, embarrassing mistakes —
   see the `FSM` timezone case (a Micronesia file that accidentally used
   the Solomon Islands' zone).
7a. **`landmarks`/`animals`/`culturalTraits`/`traditionalDishes` and similar
   free-text arrays — check these too, not just the sourced fields.** These
   fields carry no `sourceId` at all, so `validate.py` cannot catch a wrong
   or invented entry here the way it can for a `languageUsage` row — this
   makes them the single highest-yield place to find a fabricated or
   misplaced fact, and a reviewer who only checks `sourceId`-bearing fields
   will systematically miss this whole category. Confirmed patterns from
   past batches: a landmark placed in the wrong curated region (Songdo
   International Business District, actually in Incheon, filed under
   Gyeonggi in `KOR/KR-41`; the Amami rabbit, endemic to Kagoshima
   Prefecture, listed as Okinawa wildlife in `JPN/JP-47`; Kantajew Temple,
   in Rangpur Division, listed under Rajshahi in `BGD/BD-E`), a real
   landmark attributed to the wrong city (the Shwedagon Pagoda, in Yangon,
   described as being "of Mandalay" in `MMR`), and an entry that does not
   correspond to any real place at all (a "Taunggyi Oil Field" invented for
   Myanmar's Shan State — Taunggyi is the state capital, not an oil town;
   "Afulu" as a name for Tainan's real Anping Yacht Marina in `TWN`). For
   any landmark, animal or dish you don't already know to be real, a single
   web search for the name plus the region it's attributed to is normally
   enough to confirm or refute it — do this for at least a sample per file,
   not zero.
8. **Plain language, not schema jargon** (`CONTRIBUTING.md` rule 4) — do
   `note`/comment fields read naturally to someone who's never seen this
   schema, or do they lean on internal vocabulary (`locallySpoken`,
   `official-domain`, `domain=official`) as if it were prose?
9. **Unused `sources[]` entries** — is every declared source actually
   referenced by some field's `sourceId`? Not forbidden by the schema, but
   worth flagging as noise, especially when the unused source is exactly
   the one that would substantiate a classification decision if it were
   linked.

## Severity scale for findings

Use these three labels, not a bespoke scale per report — makes findings
comparable across audits and easy to triage:

- **`[data]`** — a value that's actually wrong, internally contradictory, or
  unsupported by anything in the file. Fix the number/claim.
- **`[provenance]`** — a `publisher`/`url`/`note` mismatch, or a source
  that's the wrong kind of document for what it's cited to establish. Fix
  the citation, not necessarily the value (which may well be correct).
- **`[hygiene]`** — unused sources, jargon, minor arithmetic drift, a weak
  but not wrong citation (a homepage instead of the specific page). Worth
  cleaning up, not blocking.

Don't use "BLOCKING" for something the rules don't actually forbid — that
inflates a report's apparent severity and makes genuine `[data]`/
`[provenance]` findings harder to distinguish from noise. If you're not
sure a finding maps to an actual rule, say so explicitly rather than
asserting it as a violation.

## Verifying a statistic independently

Where feasible, spot-check at least one or two load-bearing figures per
file against an independent source (a web search, a fetch of the cited
page) rather than only checking that a citation *exists*. This dataset's
own history shows the difference: purely structural review (schema valid,
sources present) has repeatedly missed real errors — a wrong percentage
for the cited report year, a share three times larger than the file's own
other claim, a timezone belonging to a different country — that a single
independent check would have caught immediately. A citation existing is
necessary, not sufficient.

## Reporting findings

Reference the exact file and line/field, quote the relevant `note` or
comment rather than paraphrasing it, and state clearly whether a finding
is confirmed by direct verification (opened the URL, ran the arithmetic,
cross-checked an independent source) or is a plausibility concern worth a
second look. A report that can't be traced back to a specific rule or a
specific verified fact isn't actionable — the goal is a list someone can
work through and close out, not a general impression.
