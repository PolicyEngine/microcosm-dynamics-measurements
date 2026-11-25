# SSA Detailed Calculator console experiment

This builds SSA's public Detailed Calculator source with Apple clang, without
its graphical interface. Credit: **Social Security Administration, Actuarial
Services**; see [LICENCE-NOTES.md](LICENCE-NOTES.md).

[PROGRESS.md](PROGRESS.md) records the measured results and example differences.
[COVERAGE.md](COVERAGE.md) maps source arithmetic to batch outputs, including
rules the batch path does not apply. This archive's computation base year is
2025, whereas the pinned guide/sample data use 2026. Successful execution does
not certify all statutory rules or historical branches.

Run from the assigned workspace's root on macOS:

```sh
./anypia/fetch.sh
./anypia/build.sh
UV_CACHE_DIR="$PWD/anypia/work/uv-cache" uv run --with pytest --with hypothesis \
  pytest anypia/tests
UV_CACHE_DIR="$PWD/anypia/work/uv-cache" uv run --with pytest --with hypothesis \
  anypia/run_cases.py --count 1000 --seed 0 --output anypia/work/generated.jsonl
```

Redirect long test/runner invocations to `anypia/work/` logs and append their
exit codes, as in the commands recorded in PROGRESS.md. Fetch/build scripts
already log themselves there. `fetch.sh --verify` checks existing pinned
downloads. `build.sh` safely unpacks sources and only the required Boost header
closure, applies the recorded report-formatting patch in `work/ported/`, and
builds `work/build/anypiab` plus SSA's embedded sample `work/build/anypiatest`.
Builds use at most four compiler workers; tests use one worker.

The Boost archive is 118,797,750 bytes; the extracted header closure is
17,153,416 bytes, below the enforced 200 MB extraction limit. Source ZIP
expansion also has a 200 MB cap. Downloaded archives are untrusted data; the
supplied Windows executable in the sample archive is never extracted or run.
Only executables compiled locally from source are executed.

`SOURCES.tsv` pins all 14 response bodies, including Wayback discovery metadata,
six SSA artifacts, Boost checksum metadata, and Boost source. Discovery metadata
can change when Wayback gains a snapshot: the script deliberately fails hash
verification rather than accepting changed bytes. Review any changed pin before
updating it. Downloaded gzip entities are retained byte-for-byte; derived PDF
and HTML are decoded locally.

`downloads/`, `vendor/`, and `work/` are ignored by git. Published fixtures retain
SSA's sample data and guide amounts independently of observed runs. The codec
and runner use Python's standard library. Tests additionally require pytest and
Hypothesis, provided through the requested `uv run` invocation. See
[FORMAT.md](FORMAT.md) for typed JSON inputs, fixed-width records, outputs, and
unsupported projection records.
