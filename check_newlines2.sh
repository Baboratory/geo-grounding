#!/bin/bash
find data/countries/ITA data/countries/GBR -name '*.yaml' | sort | while read f; do
  last=$(tail -c1 "$f" 2>/dev/null | od -An -c | tr -d ' \n')
  if [ "$last" = "\\n" ]; then
    echo "OK   $f"
  else
    echo "MISS $f (last=$last)"
  fi
done