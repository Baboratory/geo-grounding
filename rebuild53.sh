#!/bin/bash
set -e
cd /workspace/geo-grounding
# fresh main
git checkout main 2>&1 | tail -1
git reset --hard origin/main 2>&1 | tail -1
# fresh branch off main
git checkout -b batch-53-clean 2>&1 | tail -1
# bring pyproject fix from batch-52
git checkout batch-52/add-rus-ukr -- pyproject.toml
# bring only my 17 files (data + 2 language files) from the old branch
for f in \
  data/countries/SAU/country.yaml \
  data/countries/SAU/distinct-regions/whole.yaml \
  data/countries/SAU/distinct-regions/sa-01.yaml \
  data/countries/SAU/distinct-regions/sa-02.yaml \
  data/countries/SAU/distinct-regions/sa-04.yaml \
  data/countries/ARE/country.yaml \
  data/countries/ARE/distinct-regions/whole.yaml \
  data/countries/ARE/distinct-regions/ae-az.yaml \
  data/countries/ARE/distinct-regions/ae-du.yaml \
  data/countries/ARE/distinct-regions/ae-sh.yaml \
  data/countries/YEM/country.yaml \
  data/countries/YEM/distinct-regions/whole.yaml \
  data/countries/YEM/distinct-regions/ye-sn.yaml \
  data/countries/YEM/distinct-regions/ye-ad.yaml \
  data/countries/YEM/distinct-regions/ye-hd.yaml \
  data/languages/ara.yaml \
  data/languages/hin.yaml ; do
  git checkout batch-53/add-sau-are-yem -- "$f"
done
git status --short