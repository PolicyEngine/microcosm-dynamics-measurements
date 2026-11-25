`guide-examples.json` contains the amounts transcribed by text extraction from
SSA's *Social Security Benefit Calculator User's Guide*, PDF pages 65–75,
Wayback snapshot `20260824100959`. Its examples explicitly use computation year
2026. The extraction was checked to contain each sample number 1 through 30.
Amounts are decimal strings, retained independently of the built calculator's
results.

`batch-examples.pia` is the data-only `anypiab.pia` member of the pinned
`anypiabz.zip` download recorded in `../../SOURCES.tsv`. It contains exactly the
same 30 numbered examples. Its record 40 assumption years are 2026. The shipped
executable was neither extracted nor run. This small fixture copy is retained so
the numeric checks remain reviewable without the ignored vendor directory.

The pinned calculator source instead declares `BaseYearNonFile::YEAR = 2025`
and `TR_YEAR = 2025`. Tests retain the documented 2026 outputs. They record all
actual comparisons under `../../work/examples/`; mismatches on inputs declaring
2026 assumptions are marked as expected failures with the actual differences,
not replaced by new golden results. This version difference is evidence for a
possible cause, not proof that a specific numerical discrepancy has that cause.

SSA's source also embeds a different “Sample 1” in `AnypiaTestDoc`, without
documented expected amounts. It is a separate source example, not a duplicate of
the guide's sample 1, and is reported separately from the 30 numeric baselines.
`embedded-source-sample.pia` translates the exact assignments at
`vendor/anypiab/anypiatestdoc.cpp:133–157` into records. In particular the source
calls `setFirstYear(2004)` after initially calling it with 1962, so only 2004
is a maximum-earnings input year and earlier years are projected backward
with average wage increases. The source sets pre-1978 total and post-1950
quarters to 64; record 95 preserves both values. Record 40 uses 2025, the
source's computation year. This is a translation read from code, not a
reconstruction of the unrelated guide sample.
When `work/build/anypiatest` exists, the test runs the native `AnypiaTestDoc`
entry point; the translated input is a fallback for builds that produce only
`anypiab`. The execution route is recorded in the comparison JSON.

For the five post-1973 widow examples, a family output row with method `W`
exposes the selected reindexed PIA in its `fullBenefit` column: source
`piadata/piacal.cpp:205–214` assigns `widowMethod.piaEnt * benefitFactor`, and
`piadata/piaparms.cpp:1198–1240` sets that factor to 1.0 for these dates. This
mapping is read from code. The ordinary wage-indexed PIA in guide sample 22
is absent from the enabled one-page report; its selected childcare PIA and
monthly benefit are compared, with that remaining field explicitly marked
unavailable.

Calculator source credit: Social Security Administration, Actuarial Services.
