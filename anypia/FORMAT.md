# Batch case format and JSON adapter

This describes the pinned source, read directly, rather than a guessed input format.
Paths below are relative to `anypia/`; downloads/vendor directories are intentionally
ignored by git and are recreated by `fetch.sh` and `build.sh`.

## Launch contract

The build defines `ANYPIAB` and `ONEBIGFILE`. In a working directory containing
`case.pia`, send `case\n` on stdin. The program changes the supplied extension to
`.pia`, reads records until another record `01` or EOF, and writes `output` in the
working directory. It overwrites that file. Its input buffer is only 80 characters,
so use a short local stem. Source: `vendor/anypiab/anypiabdoc.cpp:137–175` and
`:188–245`. No arguments carry case values. Without `ONEBIGFILE` the alternate
source configuration accepts a list of file stems; the Python runner works with
both configurations by isolating one case per process.

Normal return code is 0; 1 stops processing (for example an input-open error); 2
means the program caught a case read/calculation error. These are not signal
codes. The runner counts 1, 2, or a normal empty output as **refused**, a nonstandard
exit/signal/timeout or undecodable numeric output as **crashed**, and a decoded
benefit result as **ran**. An uninsured `F` result is still a run. This classification
is our runner's convention, not SSA's terminology. Full stdout, stderr and output
are retained in JSON and per-case work directories.

## Records

Each line starts with a two-column decimal record number, conventionally zero
padded. There is no separating delimiter; spaces inside fields are significant.
Default earnings fields are 11 columns. Source: `vendor/oactobjs32/piadata/piaread.cpp:24–27`.
The first record must be `01`. Blank lines terminate a case, so the typed adapter
rejects them. A following `01` starts another case. Source: `piaread.cpp:58–126`.
All date strings are US order with leading zeros: `MMDDYYYY` for full dates,
`MMYYYY` for month/year. Source: `vendor/oactobjs32/misc/DateFormatter.cpp:47–79`
and `:170–205`. The typed serializer always ends every record with a newline.

Positions below are **one-based within the payload after the two-digit record
number**, inclusive. The adapter supports the following records as typed fields.

| Record | Payload positions and meaning | Source evidence |
| --- | --- | --- |
| 01 | 1–9 synthetic SSN identifier, 10 sex (`0` male, `1` female), 11–18 birth `MMDDYYYY` | `piaread.cpp:316–325`; `include/Sex.h:16–19` |
| 02 | 1–8 worker death `MMDDYYYY`; legacy six-column death months exist but the adapter uses full dates | `piaread.cpp:345–362` |
| 03 | 1 benefit type (`1` retired worker, `2` survivor family, `3` disabled worker); 2–7 entitlement `MMYYYY` for a living worker | `piaread.cpp:375–385`; `include/WorkerDataGeneral.h:47–53` |
| 04 | 1–6 month for which benefits are calculated (`MMYYYY`). Sets recalculation flag. Required for survivors. Otherwise omission uses initial entitlement month | `piaread.cpp:370–402` |
| 06 | 1–4 first earnings year, 5–8 last earnings year | `piaread.cpp:419–427` |
| 09, 10 | Most recent/second-most-recent disability period: 1–8 onset `MMDDYYYY`, 9–14 disability entitlement `MMYYYY`, 15–20 first waiting-period month `MMYYYY`; prior periods also have 21–26 cessation `MMYYYY`, 27–36 PIA at cessation, 37–46 MFB at cessation | `piadata/DisabPeriod.cpp:171–257`; `piaread.cpp:454–529` |
| 16 | Worker name, rest of line; use ASCII | `piaread.cpp:636–639` |
| 22–29 | Up to ten earnings amounts per row, each right-aligned in 11 columns, two decimal places. First year is record 06's first year + `10 × (record−22)` when projection records are absent | `piadata/piareadAny.cpp:183–197`; `piadata/piawriteAny.cpp:150–158` |
| 69–83 | Up to fifteen consecutive family members. 1–2 BIC, 3–10 birth `MMDDYYYY`, 11–16 entitlement `MMYYYY`, and only for BIC `W`, 17–24 onset `MMDDYYYY` | `piaread.cpp:539–561` |

Survivor cases ignore a worker entitlement in record 03; family-member entitlement
dates govern. The adapter therefore represents worker entitlement as `None` for
survivors and emits just `032`. For current disabled workers record 09 has only
the first twenty payload columns. Prior disability periods include cessation and
amounts. Record 10 is the older period, not an arbitrary second event.

The family BIC has **two characters**, often a trailing space. `B ` is aged spouse,
`B2` spouse caring for a child, `B6` divorced aged spouse, `C1` etc. child, `D ` aged
widow(er), `D6` divorced aged widow(er), `E ` surviving parent caring for a child,
`W ` disabled widow(er), and `W6` divorced disabled widow(er). Source:
`piadata/Bic.cpp:13–27` and `:85–145`. The data format does not encode a family member's sex.
It must not be invented from the worker's sex or BIC.

The full vendor format also supports these records, exposed as opaque
`Case.extra_records` except where noted. Their payloads are read in
`piadata/piaread.cpp` and `piadata/piareadAny.cpp`.

| Record(s) | Meaning |
| --- | --- |
| 05 | Social Security Statement month and planned retirement age; Statement cases are outside this adapter |
| 07, 08 | Backward/forward earnings projections: type (1), percent (6), entered-span first/last year (4). These change earnings-row year offsets, so the typed adapter rejects them; use `run_raw` with a full `.pia` fixture |
| 11 | Military service periods |
| 12 | Worker noncovered pension (10 columns), optionally starting month (6) |
| 13–15 | One-column totalization, statutory blindness, deemed-insured flags |
| 17–19 | Worker address lines |
| 20 | One earnings-type digit per year: 0 entered, 1 maximum, 2 high, 3 average, 4 low; see `include/EarnProject.h:24–29` |
| 21 | One tax-type digit per year |
| 30–37 | Medicare-only earnings |
| 38 | Noncovered pension after reservist removal |
| 39 | Prior retirement entitlement and cessation months |
| 40 | Assumption start year (4), COLA assumption (1), average-wage assumption (1), wage-base method (1) |
| 41–44, 45–54, 55 | Projected benefit increases; catch-up increases; title |
| 56–59, 60 | Average-wage projections; title |
| 61–64, 65–68 | Projected regular and old-law wage bases |
| 84–94 | Railroad earnings and quarters of coverage |
| 95 | Summary total quarters (3), post-1950 quarters (3) |
| 96 | Annual quarters of coverage |
| 97 | Annual child-care-year indicators |

The Python API does **not** claim to validate all statutory eligibility or all
opaque payloads. It validates the structural typed subset and delegates SSA data
checks to the program. It accepts exact-cent, nonnegative earnings and fills
missing interior years with zero. Histories are at most 80 years within 1937–2100;
the calculator can impose tighter limits for a particular case. It fails on
duplicate records, incomplete typed fields, unsupported projection semantics,
out-of-order records, surplus earnings rows, and nonconsecutive family rows rather
than silently dropping values. The typed adapter requires increasing record-number
order: record 03 after record 04 would reset the vendor's calculation month. The legacy
format supports additional partial disability/date encodings which are outside
this intentionally explicit adapter.

## Output

For retirement/disability there is one worker row followed by zero or more family
rows. Survivors have family rows only. Every row begins `SSS-SS-SSSS MM/DD/YYYY`.
The next fields use width 8, fixed point with two decimals, and can abut without
whitespace. Source: `vendor/anypiab/anypiabdoc.cpp:283–328`.

| Row | Following fields |
| --- | --- |
| Worker | PIA, MFB, rounded worker benefit; space; fixed-width age text; space; one-character computation method; space; combined insurance `T`/`F` |
| Family | Worker PIA, worker MFB, full auxiliary/survivor benefit, rounded auxiliary/survivor benefit; space; one-character method; space; two-character BIC; space; combined insurance `T`/`F` |

The primary row does not output a BIC; the adapter labels it `A ` based on its
worker role. No AME/AIME columns are enabled in this build. Non-row lines such as
`Need annual pre-1951 earnings in prior case` are messages. Statement output has a
different layout and is outside `parse_output`'s supported domain.

The final insurance flag is a combined condition constructed in
`anypiabdoc.cpp:258–267`: some fully/totalization status codes set `F`, and a
disability case additionally requires disability-insured status. Distinct fully,
currently, and disability-insured values **are not printed**. `nonins()` and
`disinsout()` calls are commented out (`:217–219`). JSON therefore emits
`insured_status.combined` and leaves `fully`, `currently`, and `disability` null.
Those nulls mean unavailable from this output, never uninsured. All family rows
repeat the same worker insurance flag. See `COVERAGE.md` for calculation coverage.

## Python use and reproducible checks

`cases.py` is standard library only. Public types are `Case`, `Month`,
`DisabilityPeriod`, `FamilyMember`, and `BenefitType`. `dumps`/`loads` operate on a
single `.pia` case; `dumps_many`/`loads_many` operate on a concatenated batch.
`to_dict`/`from_dict` use ISO dates/months and exact decimal strings, and
`parse_output` returns a dictionary with PIA, MFB, benefit rows, insurance and
messages. `run_cases.run_case` and `run_raw` add process diagnostics.

```sh
HYPOTHESIS_STORAGE_DIRECTORY=$PWD/anypia/work/hypothesis \
UV_CACHE_DIR=$PWD/anypia/work/uv-cache \
uv run --with pytest --with hypothesis pytest -q anypia/tests \
  -o cache_dir=anypia/work/pytest-cache --basetemp=anypia/work/pytest-temp

UV_CACHE_DIR=$PWD/anypia/work/uv-cache \
uv run --with pytest --with hypothesis anypia/run_cases.py \
  --count 1000 --seed 0 --output anypia/work/generated.jsonl
```

Redirect long-command stdout/stderr to a log under `anypia/work/` and append its
exit code. The generator cycles retirement, disability and survivor families with
deterministic seeded earnings and some spouses/children. Earnings start no earlier
than 1978; entitlement/benefit dates end by 2024, avoiding forecast assumptions.
These are structurally valid ordinary families, with acceptance measured by the
actual run. They do not exhaust statutory edge cases. The runner defaults to
`work/build/anypiab`, writes per-case inputs and logs under `work/generated`, emits
one JSON line per attempted case, and saves aggregate counts in `summary.json`.
`--input PATH` accepts typed case JSONL instead of generated cases.
