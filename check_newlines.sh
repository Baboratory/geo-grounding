#!/bin/bash
NEW=$(git status --porcelain | awk '{print $2}' | grep -E 'data/.*\.yaml$')
for f in $NEW; do
  last=$(tail -c1 "$f" 2>/dev/null | od -An -c | tr -d ' \n')
  if [ "$last" = "\\n" ]; then
    echo "OK   $f"
  else
    echo "MISS $f (last=$last)"
  fi
done