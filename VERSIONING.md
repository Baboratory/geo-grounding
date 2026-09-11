# Versioning

This project is versioned (`vMAJOR.MINOR.PATCH`, [SemVer](https://semver.org/)), but the version number is about one specific thing: **whether code that already reads this dataset will keep working correctly.** It is not a measure of how much changed, how many countries got added, or how much new information landed in a release — a release that adds an entire new country is exactly as "small" a version bump as one that fixes a single typo, provided neither one changes the *shape* of the data.

## What the three numbers mean here

- **MAJOR** — something that already worked when reading this data may now break or silently misbehave. Always a change to `schema/*.json`.
- **MINOR** — a new capability was added to the schema that old reading code can safely ignore. Always a change to `schema/*.json`.
- **PATCH** — everything else: new/updated data (`data/**`), tooling, docs, examples. The schema's shape didn't change at all.

**Every commit to `main` gets its own version.** There is no such thing as "just a commit, not a release" here — if nothing in `schema/*.json` changed, the commit is an automatic PATCH bump; if it did, it's a MAJOR or MINOR bump depending on the table below. This is deliberate: it means a version number is always a precise, reproducible pointer to one exact dataset snapshot — querying `v1.4.27` today and querying `v1.4.27` a year from now returns byte-identical content, always. (Querying `main`, or a floating reference — see below — does *not* carry that guarantee, and isn't supposed to.)

## Is a schema change breaking? A concrete test

The question is never "how big is this change" — it's always: **would code that doesn't know about this change still read existing data correctly?**

| Change | Breaking? | Bump |
|---|---|---|
| New optional field/section added | No | MINOR |
| New required field added | **Yes** — old data files don't have it | MAJOR |
| Field removed | Yes | MAJOR |
| Field renamed | Yes | MAJOR |
| Field's type/shape changed (e.g. string → array) | Yes | MAJOR |
| Required field made optional | No | MINOR |
| Constraint relaxed (min↓, max↑, regex widened) | No | MINOR |
| Constraint tightened (existing data could now be invalid) | Yes | MAJOR |
| New enum value added | Usually no — but breaks a reader with an exhaustive `switch`/`case` and no default case. Flag it in the release notes either way. | MINOR (flagged) |
| New country/region/language file added | No — nothing about the format changed, just another instance of it | PATCH |
| Existing data value corrected (a statistic, a source URL, a typo) | No | PATCH |
| Previously-empty optional field filled in with real sourced data | No | PATCH |
| Change to `scripts/`, `usage_examples/`, docs | No — not part of the data contract at all | PATCH |

## Three ways to reference this project, for three different needs

| Reference | Example | Guarantees | Use it when |
|---|---|---|---|
| Exact tag | `v1.4.27` | Byte-identical forever | You need reproducibility — tests, citations, anything that must not change under you |
| Floating tag | `v1.4`, `v1` | Always the *latest* release within that MAJOR (or MAJOR.MINOR) line — moves as new PATCH/MINOR releases land, never moves across a MAJOR bump | You want the freshest data/fixes but still want a hard guarantee your code keeps working |
| `main` branch | `main` | Freshest possible, no compatibility guarantee at all — could be mid-MAJOR-bump | You always re-pull and don't mind occasionally adapting to a schema change |

Floating tags (`v1`, `v1.4`) are not real, immutable git tags in the usual sense — they're deliberately re-pointed (`git tag -f` + `git push --force`) to the latest matching exact tag every time one is cut. That's a standard pattern (it's how `actions/checkout@v4` and Docker's `image:2` tag work too): the exact tag underneath is still permanent, only the floating alias moves.

## See also

- [DESIGN.md](DESIGN.md) — why the schema is shaped the way it is; read this before deciding whether a change you're making is additive or breaking.
- [CONTRIBUTING.md](CONTRIBUTING.md) — how to propose a change.
