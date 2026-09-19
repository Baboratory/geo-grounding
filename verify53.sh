#!/bin/bash
cd /workspace/geo-grounding
echo "=== non-yaml/non-pyproject files committed (should be empty) ==="
git show --name-only --pretty=format: HEAD | grep -vE '^$|\.yaml$|pyproject\.toml' || echo "(none)"
echo "=== committed file count ==="
git show --name-only --pretty=format: HEAD | grep -cE '\.yaml$'
echo "=== trailing-byte of committed blobs (expect 0a) ==="
for f in data/countries/SAU/country.yaml data/countries/ARE/country.yaml data/countries/YEM/country.yaml data/countries/SAU/distinct-regions/whole.yaml data/countries/ARE/distinct-regions/whole.yaml data/countries/YEM/distinct-regions/whole.yaml data/languages/ara.yaml data/languages/hin.yaml; do
  b=$(git show HEAD:$f | tail -c1 | od -An -t x1 | tr -d ' \n')
  echo "$f : $b"
done