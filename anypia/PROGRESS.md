ANYPIA: BUILT

Pinned **8 artifact bodies** (6 SSA files, Boost source, Boost checksum metadata), plus **6 Wayback availability responses**: **14 rows in SOURCES.tsv**. All 14 were downloaded again through `fetch.sh` and their sizes and SHA-256 hashes verified.

Coverage: **39 computed / 3 not computed / 3 input only** (45 rows). **Family maximum: computed and applied. Insured status: fully/currently/disability computed internally; stock output exposes combined eligibility only. Earnings test: not applied by the batch path** (inferred from source path inspection). GPO and widow(er)'s RIB-LIM are also absent from the calculation path (source-inspection inferences).

Examples: **22 of 30 documented guide cases fully reproduced**; one partial comparison and seven numerical differences. All **31 distinct examples ran** (30 shipped/guide cases plus SSA's separate embedded source sample); **0 refused, 0 crashed**. The embedded sample has no documented numeric baseline. Source base year 2025 versus guide/input 2026 is a possible explanation for differences, **not a proved cause**.

Generated cases: **1,000 attempted; 1,000 ran; 0 refused; 0 crashed**, seed 0. Composition: 334 retirement, 333 disability, 333 survivor families. Audited all **1,853 benefit rows** against input family counts and identifiers.

Patch: **`patches/0001-console-resource-strings.patch`** — replace MFC-only string formatting required to link the stock DETAILS report, using SSA's resource strings. **Zero calculation lines changed.** Original vendor files remain intact.

No commits or pushes were made, following the task-specific instruction. Downloads, vendor sources, build products, and run evidence are kept in their ignored directories; reproducible scripts, independent fixtures, tests, and reports are ready for the dispatching session.

## Task 1 — Fetch and pin

Completed. Pinned five SSA artifacts: source page (`20260831011110`), batch page (`20260831011110`), calculation ZIP (`20250902042939`), interface/console source ZIP (`20250902043021`), and guide (`20260824100959`). `SOURCES.tsv` also records availability-API responses and Boost release metadata. Downloads are treated as untrusted data; no supplied executable is run. Safe ZIP extraction succeeded; traversal, symlinks, and source expansion over 200 MB are rejected. `fetch.sh` repeats downloads and verifies byte counts and SHA-256; `--verify` checks local pins.

## Task 2 — Licence

Completed. `LICENCE-NOTES.md` quotes the guide's copyright/distribution statement, PDF page 3, with snapshot and digest. SSA Actuarial Services is acknowledged.

## Task 3 — Coverage

Completed: `COVERAGE.md` has 45 rows: **39 computed, 3 not computed, 3 input only**, with file-and-line evidence read from the source. Family maximums are computed and applied. Fully/currently/disability insured statuses are computed internally; stock batch output exposes only combined eligibility. Retirement earnings test and widow(er)'s limit have no call in the batch calculation path. Government pension offset is not implemented in that path. These are source-read findings, not results inferred from class names.

## Task 4 — Build

Completed using Apple clang 21.0.0, C++14, and the stock `ANYPIAB`, `ONEBIGFILE`, `DETAILS` macros. Compiled and linked **231/231 translation units** into `work/build/anypiab`; `work/build.log` ends `EXIT_CODE=0`. Before fetching Boost, the includes were read: date/time Gregorian/local time and serialization access/base_object. Boost 1.81.0 archive size **118,797,750 bytes** was obtained by HEAD and announced before download; the published SHA-256 matched. Extracted only a conservative transitive header closure (including macro-selected configuration/preprocessor/MPL headers): **1,767 headers, 17,153,416 bytes**, below the 200 MB cap. No Boost tool or bundled executable is run.

Patch: `patches/0001-console-resource-strings.patch` replaces MFC-only string formatting needed to link the stock DETAILS report. Its lookup is generated from SSA's original resource strings. It affects one interface source file in `work/ported/`, leaving `vendor/` untouched and changing **zero calculation lines**. The other port choices are build configuration: existing standard-bitset Windows support files without defining WIN32, and correct source include directories. No calculation patch or algorithm substitution was needed.

## Task 5 — SSA examples

Completed. All 30 sample cases were read from the pinned SSA `.pia` input archive, and all 30 documented numerical baselines were independently transcribed from the guide (PDF pages 65–75). Tests retain the expected amounts instead of replacing them with calculator output. All 30 ran without refusal/crash. **22 fully reproduced; 1 partial; 7 numerically different**. The seven differences all involve sample inputs carrying 2026 assumptions while the pinned source sets base year 2025; this correlation is read/observed, and attributing the differences to it remains an inference.

The separate embedded sample is run directly by compiling SSA's stock `main` without `ANYPIAB`, then compared to its exact batch-record translation. Both ran and agreed: PIA $1,939.00, MFB $3,394.10, worker benefit $1,939.00. There is no documented numeric baseline for that sample, so it is counted as execution, not independent reproduction.

The table below records all guide comparisons. Sample 22's selected child-care PIA and benefit match, but its ordinary PIA is not printed by the enabled output. Seven numerical mismatches and the one missing field are explicit pytest expected failures, never counted as passes. Detailed observed/expected fields and messages are retained under `work/examples/` and `work/example-results.json`.

| Guide sample | Result | Differences / unavailable fields |
|---|---|---|
| 1 (PDF p. 65) | Documented output differs | PIA: expected 4968.50, observed 4982.40; MBA: expected 4968.00, observed 4982.00 |
| 2 (PDF p. 65) | Documented output differs | PIA: expected 4254.20, observed 4063.30; MBA: expected 4254.00, observed 4063.00 |
| 3 (PDF p. 65) | All documented fields reproduced | — |
| 4 (PDF p. 66) | All documented fields reproduced | — |
| 5 (PDF p. 66) | Documented output differs | regular PIA: expected 441.70, observed 440.40; re-indexed widow(er) guarantee PIA: expected 477.20, observed 478.20 |
| 6 (PDF p. 66) | All documented fields reproduced | — |
| 7 (PDF p. 67) | All documented fields reproduced | — |
| 8 (PDF p. 67) | Documented output differs | PIA: expected 12782.50, observed 12474.60; MBA: expected 12782.00, observed 12474.00 |
| 9 (PDF p. 67) | All documented fields reproduced | — |
| 10 (PDF p. 68) | Documented output differs | PIA: expected 1562.90, observed 1492.30; MBA: expected 1100.00, observed 1050.00 |
| 11 (PDF p. 68) | All documented fields reproduced | — |
| 12 (PDF p. 68) | All documented fields reproduced | — |
| 13 (PDF p. 69) | All documented fields reproduced | — |
| 14 (PDF p. 69) | All documented fields reproduced | — |
| 15 (PDF p. 69) | All documented fields reproduced | — |
| 16 (PDF p. 70) | All documented fields reproduced | — |
| 17 (PDF p. 70) | All documented fields reproduced | — |
| 18 (PDF p. 70) | Documented output differs | PIA: expected 3478.50, observed 3383.80; MBA: expected 4313.00, observed 4195.00 |
| 19 (PDF p. 71) | All documented fields reproduced | — |
| 20 (PDF p. 71) | All documented fields reproduced | — |
| 21 (PDF p. 72) | Documented output differs | PIA: expected 3826.10, observed 3714.00; MBA: expected 3826.00, observed 3714.00 |
| 22 (PDF p. 72) | All emitted fields match; partial comparison | not emitted: regular PIA |
| 23 (PDF p. 72) | All documented fields reproduced | — |
| 24 (PDF p. 73) | All documented fields reproduced | — |
| 25 (PDF p. 73) | All documented fields reproduced | — |
| 26 (PDF p. 73) | All documented fields reproduced | — |
| 27 (PDF p. 74) | All documented fields reproduced | — |
| 28 (PDF p. 74) | All documented fields reproduced | — |
| 29 (PDF p. 74) | All documented fields reproduced | — |
| 30 (PDF p. 75) | All documented fields reproduced | — |


## Additional sample data provenance

The source archives lack the `.pia`/`.dat` sample files promised by the source page. Pinned the batch page's `anypiabz.zip` (`20260824101400`), 318,507 bytes, and extracted **only** `anypiab.pia` into `vendor/samples/`; the supplied executable stays inside the archive and is never run. `SOURCES.tsv` now contains 14 downloaded response rows: six SSA artifacts, six availability-API responses, Boost release checksum metadata, and the Boost source archive. The guide computes examples at 2026; the pinned source's base year is 2025. Comparison must retain this version gap.

## Task 6 — Input/output adapter

Completed. `FORMAT.md` describes the batch launch contract, fixed-width records, source lines, output fields, and supported subset. `cases.py` is standard library only: typed exact-cent earnings, birth/sex, entitlement/benefit dates, disability onset/waiting/cessation, death, and family members; single/batch serializers and parsers; typed JSON conversion; output parsing; and a seeded family generator. Projection records 07/08 change earnings indexing and are explicitly rejected by the typed subset; original raw `.pia` records remain usable through `run_raw`. Granular insurance components remain JSON null because stock output does not expose them; combined eligibility is retained.

Hypothesis round-trip properties and edge regressions pass, including decimal widths, paired disability records, record ordering, extra-record preservation, family indexing, and malformed output. Live integration passes. All 124 documentation source references were checked for existing files, and the format reference ranges were corrected after review. `work/cases-live-tests.log` records 14 passing tests before the final classification regressions; `work/cases-classification-tests.log` records **18 passed**, `EXIT_CODE=0`. SSA exit codes 1 and 2 count as refused; signals, unexpected exit codes, timeouts, and parser failures count as crashed.

## Task 7 — Runner and generated cases

Completed. `run_cases.py` writes one input and executes the locally built binary in each isolated case directory, preserving calculator output/stdout/stderr and messages. It emits one JSON line per case with the inputs, PIA, MFB, each benefit, and available insurance results. Its status convention distinguishes decoded results, caught case refusals, and crashes/timeouts/parser errors; uninsured results still count as runs. Six review checks exercised normal, refused, empty-output, signal, malformed-output and timeout paths.

Authoritative command (stdout/stderr redirected to `work/generated.log`, which ends `EXIT_CODE=0`):

```sh
UV_CACHE_DIR="$PWD/anypia/work/uv-cache" uv run --with pytest --with hypothesis \
  anypia/run_cases.py --count 1000 --seed 0 --output anypia/work/generated.jsonl
```

| Family kind | Attempted | Ran | Refused | Crashed |
|---|---:|---:|---:|---:|
| Retired worker | 334 | 334 | 0 | 0 |
| Disabled worker | 333 | 333 | 0 | 0 |
| Survivor | 333 | 333 | 0 | 0 |
| Total | 1,000 | 1,000 | 0 | 0 |

`work/generated/summary.json` and `work/generated.jsonl` contain results. An independent audit verified all 1,853 expected worker/family rows, identifiers, PIA/MFB availability, and combined insured flags (`work/generated-audit.log`, `EXIT_CODE=0`). These ordinary families use historical dates to avoid forecast assumptions; acceptance is measured, and this run does not establish coverage of all historical/statutory branches.

## Final verification

Final combined pytest result: **42 passed, 8 xfailed**, `EXIT_CODE=0` (`work/tests.log`). The eight expected failures are the seven independently documented numerical differences plus one unprinted guide comparison field; they are reported above and are not successful reproductions.

```sh
UV_CACHE_DIR="$PWD/anypia/work/uv-cache" \
HYPOTHESIS_STORAGE_DIRECTORY="$PWD/anypia/work/hypothesis" \
uv run --with pytest --with hypothesis pytest -c anypia/pytest.ini -q anypia/tests
```

The full pinned fetch was repeated successfully (`work/fetch.log`, `EXIT_CODE=0`); local verification logs are separate (`work/fetch-verify.log`). The final build and native source sample link succeeded (`work/build.log`, `EXIT_CODE=0`). Audited all **588 original vendor source files** against the two pinned ZIP archives: every byte remains unchanged (`work/vendor-audit.log`, `EXIT_CODE=0`). Build logs retain inherited capitalization warnings in SSA include paths on this host; they did not prevent compilation/linking. No supplied binary was executed, no calculation source was patched, and all retained task files are under `anypia/`.
