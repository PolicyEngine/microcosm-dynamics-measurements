#!/bin/bash
# Repeat pinned downloads. Never execute anything from a downloaded archive.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p anypia/downloads anypia/work
verify_only=false
if [[ ${1:-} == --verify ]]; then verify_only=true; fi
log=anypia/work/fetch.log
if $verify_only; then log=anypia/work/fetch-verify.log; fi
exec >"$log" 2>&1
trap 'rc=$?; printf "\nEXIT_CODE=%s\n" "$rc"' EXIT
while IFS=$'\t' read -r original snapshot bytes digest target request notes; do
    [[ $original == original_url ]] && continue
    [[ $target == anypia/downloads/* ]] || { echo "Unsafe destination: $target"; exit 1; }
    if ! $verify_only; then
        echo "Fetching $request"
        # Retain raw content encoding, which is part of each pinned entity.
        curl --fail --silent --show-error --connect-timeout 30 --max-time 1800 \
            "$request" -o "$target.part"
        actual=$(shasum -a 256 "$target.part" | cut -d ' ' -f 1)
        [[ $actual == "$digest" ]] || { echo "SHA256 mismatch: $target"; exit 1; }
        [[ $(wc -c < "$target.part" | tr -d ' ') == "$bytes" ]] || exit 1
        mv "$target.part" "$target"
    fi
    [[ $(shasum -a 256 "$target" | cut -d ' ' -f 1) == "$digest" ]] || exit 1
    [[ $(wc -c < "$target" | tr -d ' ') == "$bytes" ]] || exit 1
    echo "Verified $target ($bytes bytes)"
done < anypia/SOURCES.tsv
gzip -dc anypia/downloads/anypia32.pdf.gz > anypia/downloads/anypia32.pdf
gzip -dc anypia/downloads/source.html.gz > anypia/work/source.html
gzip -dc anypia/downloads/anypiab.html.gz > anypia/work/anypiab.html
echo "All pinned hashes verified. Source extraction: uv run --with pytest --with hypothesis anypia/unpack.py"
