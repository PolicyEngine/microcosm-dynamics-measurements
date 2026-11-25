#!/bin/bash
# Apple clang build; retain calculation sources unchanged in vendor/.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p anypia/work/build
exec >anypia/work/build.log 2>&1
trap 'rc=$?; printf "\nEXIT_CODE=%s\n" "$rc"' EXIT
export UV_CACHE_DIR="$PWD/anypia/work/uv-cache"
./anypia/fetch.sh --verify
uv run --with pytest --with hypothesis anypia/unpack.py
if [[ ! -f anypia/vendor/boost_1_81_0/boost/date_time/gregorian/gregorian.hpp ]]; then
    uv run --with pytest --with hypothesis anypia/boost_headers.py
fi
uv run --with pytest --with hypothesis anypia/build.py "$@"
