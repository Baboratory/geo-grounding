#!/bin/bash
cd /workspace/geo-grounding
files=$(find data/countries/SAU data/countries/ARE data/countries/YEM -name '*.yaml')
files="$files data/languages/ara.yaml data/languages/hin.yaml"
for f in $files; do
  last=$(tail -c1 "$f" | od -An -t x1 | tr -d ' \n')
  if [ "$last" != "0a" ]; then
    printf '\n' >> "$f"
  fi
done
echo "=== trailing byte of each new file (expect 0a) ==="
for f in $(find data/countries/SAU data/countries/ARE data/countries/YEM data/languages/ara.yaml data/languages/hin.yaml -name '*.yaml'); do
  b=$(tail -c1 "$f" | od -An -t x1 | tr -d ' \n')
  echo "$f : $b"
done