## What this changes

<!-- one or two sentences -->

## Checklist

- [ ] `pre-commit run --all-files` passes (or individually: `black`, `ruff check`, `mypy`, `codespell`, `yamllint -c .yamllint.yaml`, `python3 scripts/validate.py`) — all with 0 errors
- [ ] Every new statistic (`ethnicGroups`, `languageUsage`, `religions`) has a `sourceId` pointing to an official source in `sources[]`
- [ ] Any field left out on purpose has a comment explaining why (see CONTRIBUTING.md)
- [ ] If a country/region was added: it has a `WHOLE` entry, and `adminUnitCodes` on every non-WHOLE region if `hasSubdivisions: true`
