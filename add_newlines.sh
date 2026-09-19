#!/bin/bash
# Ensure each authored data file ends with a trailing newline (write_file strips it).
FILES=$(git status --porcelain | awk '{print $2}' | grep -E 'data/.*\.yaml$')
for f in $FILES; do
  if [ -f "$f" ]; then
    last=$(tail -c1 "$f")
    if [ -n "$last" ]; then
      printf '\n' >> "$f"
      echo "newline added: $f"
    else
      echo "ok (has newline): $f"
    fi
  fi
done
echo "--- done ---"