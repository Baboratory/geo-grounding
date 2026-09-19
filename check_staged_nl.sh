#!/bin/bash
# Re-verify the actual COMMITTED blob ends with newline (per hard-rule loop).
for f in data/languages/cym.yaml data/languages/gla.yaml data/languages/gle.yaml data/languages/sco.yaml data/languages/srd.yaml data/countries/ITA/country.yaml data/countries/ITA/distinct-regions/whole.yaml data/countries/ITA/distinct-regions/it-25.yaml data/countries/ITA/distinct-regions/it-62.yaml data/countries/ITA/distinct-regions/it-82.yaml data/countries/GBR/country.yaml data/countries/GBR/distinct-regions/whole.yaml data/countries/GBR/distinct-regions/gb-eng.yaml data/countries/GBR/distinct-regions/gb-sct.yaml data/countries/GBR/distinct-regions/gb-wls.yaml; do
  last=$(git show :"$f" 2>/dev/null | tail -c1 | od -An -c | tr -d ' \n')
  if [ "$last" = "\\n" ]; then
    echo "OK   $f"
  else
    echo "MISS $f (last=$last)"
  fi
done