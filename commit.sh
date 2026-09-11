#!/usr/bin/env bash
# Generic, reusable commit runner — not regenerated per commit. Claude
# writes the actual commit content to commit-message.txt (gitignored,
# disposable) and hands you this same command each time: ./commit.sh
#
# Why this exists at all: commits in this repo must be authored purely
# by the Baboratory cast (see PERSONAS.md rule #3), with no AI
# co-author trailer — and Claude has a standing requirement to add one
# to any commit it runs itself. So Claude prepares commit-message.txt
# and this script, but never runs `git commit` itself; a human does,
# by running this file.
#
# commit-message.txt format:
#   Author: Name <email>
#   Committer: Name <email>        <- optional, defaults to Author
#   <blank line>
#   <commit subject>
#   <blank line>
#   <commit body...>
#
# Committer only needs to be spelled out when it differs from Author —
# e.g. porting an external contribution (see PERSONAS.md rule #5 and
# MAINTAINING.md): Author is the real contributor (so it counts on
# their GitHub contribution graph once this reaches a public repo),
# Committer is the persona who reviewed/integrated it. Every other
# commit just needs the one Author line, same as before.
#
# On a successful commit, commit-message.txt is deleted (consumed) so
# a stale message can't accidentally get re-committed later. On
# failure (e.g. git commit errors out), it's left in place so you can
# inspect it and retry.
set -euo pipefail
cd "$(dirname "$0")"

MSG_FILE="commit-message.txt"

if [[ ! -f "$MSG_FILE" ]]; then
  echo "No $MSG_FILE found — nothing for me to commit. Ask Claude to prepare one." >&2
  exit 1
fi

author_name=""
author_email=""
committer_name=""
committer_email=""
header_lines=0

while IFS= read -r line; do
  header_lines=$((header_lines + 1))
  if [[ -z "$line" ]]; then
    break
  elif [[ "$line" =~ ^Author:\ (.+)\ \<(.+)\>$ ]]; then
    author_name="${BASH_REMATCH[1]}"
    author_email="${BASH_REMATCH[2]}"
  elif [[ "$line" =~ ^Committer:\ (.+)\ \<(.+)\>$ ]]; then
    committer_name="${BASH_REMATCH[1]}"
    committer_email="${BASH_REMATCH[2]}"
  else
    echo "Unrecognized header line in $MSG_FILE (expected 'Author:' or 'Committer:', or a blank line to end the header):" >&2
    echo "  $line" >&2
    exit 1
  fi
done <"$MSG_FILE"

if [[ -z "$author_name" ]]; then
  echo "$MSG_FILE must start with 'Author: Name <email>'." >&2
  exit 1
fi
if [[ -z "$committer_name" ]]; then
  committer_name="$author_name"
  committer_email="$author_email"
fi

# Everything after the header's blank line is the actual git commit
# message (subject + body).
body="$(tail -n +$((header_lines + 1)) "$MSG_FILE")"

git add -A

GIT_AUTHOR_NAME="$author_name" \
GIT_AUTHOR_EMAIL="$author_email" \
GIT_COMMITTER_NAME="$committer_name" \
GIT_COMMITTER_EMAIL="$committer_email" \
git commit -m "$body"

rm "$MSG_FILE"
echo "Committed — Author: $author_name <$author_email>, Committer: $committer_name <$committer_email>. Removed $MSG_FILE."
git log --oneline -1
