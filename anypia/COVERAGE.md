# Detailed Calculator calculation coverage

**Source-read totals: 39 computed, 3 not computed, 3 input only (45 rows).**

The family maximum is computed, selected with the applicable PIA method, and
applied to family benefits. Fully, currently, and disability insured status are
computed internally. The unmodified console output exposes only a combined
insured `T`/`F`; it does not identify those three statuses separately. The
retirement earnings test, government pension offset, and widow(er)'s RIB-LIM
are **not applied by the batch calculation path**. The source includes unused
earnings-test and RIB-LIM functions; their presence alone is not coverage.

This is a code inspection of the pinned SSA source, not a claim that every
branch has been validated against an independent oracle. `Computed` means
arithmetic is reachable from `AnypiabDoc::calculate`; `input only` means the
program accepts an already determined fact or amount; `not computed` means
the batch path does not implement/apply the rule. Absence findings below are
explicitly identified as inferences from the complete path and symbol searches.
Examples and generated-case execution are reported separately in PROGRESS.md.

Paths in the table are relative to `anypia/`. `D/` abbreviates
`vendor/oactobjs32/piadata/`; `H/` abbreviates `vendor/oactobjs32/include/`;
`B/` abbreviates `vendor/anypiab/`. Line numbers refer to the downloaded source
(portability patches may move lines in the working copy).

The active path is `B/anypiabdoc.cpp:201-216` → `PiaCalAny::calculate2`
(`D/piacalany.cpp:165-190`) → `PiaCalPL::piaCal`
(`D/PiaCalPL.cpp:54-130`), followed by widow reindexing and `PiaCal::piaCal3`.
`PiaCalPL::piaCal:69-126` constructs applicable methods and calls each method's
`calculate()`. `D/piacal.cpp:298-330` selects the greatest PIA and the MFB
associated with that PIA; it does **not** simply select the largest MFB across
methods.

Stock output fields used below are actual members written by
`B/anypiabdoc.cpp:258-328`:

- `PIA` = `piaData->highPia` (worker and family rows, lines 287/320).
- `MFB` = `piaData->highMfb` (lines 288/321).
- `worker benefit` = `piaData->roundedBenefit` (line 289).
- `family full benefit` = `Secondary::getFullBenefit()` (line 323), before
  family-maximum and age reductions; `family benefit` =
  `Secondary::getRoundedBenefit()` (line 324), after those reductions.
- `PIFC` = the method code, lines 310/325; `BIC` = beneficiary category,
  line 327; `insured` = combined `insStat`, lines 260-268 and 313/328.

Individual losing methods' PIAs/MFBs and intermediate calculation values are
not separate fields in stock output. A method row saying `PIA`/`MFB` means
its result is carried there **if selected**, not that every method result is
printed. Family rows repeat the worker's PIA/MFB; a higher reindexed widow's
PIA can instead be reflected in her benefit and `PIFC=W`.

| Rule | Status | Read evidence and actual operation | Stock batch output carrying result |
|---|---|---|---|
| Wage-indexed PIA (1977 amendments) | computed | `D/WageInd.cpp:98-123` indexes earnings, selects high years, computes AIME, portions it at bend points, and evaluates PIA. `D/PiaMethod.cpp:340-355` divides selected earnings by `12*N`; `D/WageIndGeneral.cpp:196-203` sums formula portions times percentages. | PIA; PIFC; worker/family benefit |
| Old-start PIA, including historical amendment variants | computed | `D/oldstart.cpp:129-162` selects the amendment method, imputes pre-1951 earnings, selects years, applies two formula percentages and increment years; `:165-219` chooses 1939/1950/1958 conversion branches or the frozen December 1978 table; `:250-277` applies later table/increase rules. | PIA; PIFC |
| PIA-table / new-start historical PIA | computed | `D/PiaTable.cpp:106-133` excludes freeze years, orders earnings, computes AME, evaluates `oldPiaCal`/`cpiBase`, and saves `piasub`. `D/oldpia.cpp:39-60` dispatches historical amendment tables; `:74-189` extends/increases the table. | PIA; PIFC |
| Transitional guarantee PIA | computed | `D/TransGuar.cpp:93-121` uses pre-eligibility earnings, selects high years, evaluates the frozen December 1978 PIA table and applies post-eligibility COLAs. Applicability is tested at `:66-87`. | PIA; PIFC |
| Special minimum PIA | computed | `D/SpecMin.cpp:98-141` counts coverage years, caps excess years, obtains the date-specific special-minimum PIA, or multiplies excess years by the earlier minimum amount; `:162-164` limits usable years. `D/PiaMethod.cpp:138-150` compares earnings to coverage thresholds. | PIA; PIFC |
| Frozen minimum PIA | computed | `D/FrozMin.cpp:77-84,96-107` initializes $122, sets the increase starting year using entitlement/death and age 65, then applies COLAs. | PIA; PIFC |
| Child-care dropout PIA | computed | `D/ChildCareCalc.cpp:103-128` indexes/selects earnings, reduces computation years by qualifying child-care dropout years, recalculates AIME and formula PIA. `:149-211` tests supplied child-care flags and allowed earnings, and swaps/selects years. | PIA; PIFC |
| Disability PIA guarantee | computed | `D/DibGuar.cpp:95-109` selects the prior disability period, tests the benefit gap, starts from the **input** cessation PIA, and applies the appropriate COLAs. This computes the guarantee from prior supplied amounts, not the original prior award. | PIA; PIFC |
| Reindexed widow(er) PIA | computed | `D/PiaCalPL.cpp:169-177` constructs and calculates applicable widow methods; `D/ReindWid.cpp:113-153,165-179` reindexes earnings, selects high years and evaluates/increases a widow-specific PIA. `D/piacal.cpp:205-215` substitutes it when higher. | family full benefit, family benefit, PIFC `W`; family row's PIA field still repeats worker PIA |
| Wage-indexed PIA without disability freeze | computed | `D/WageIndNonFreeze.cpp:60-83` tests non-freeze insured status/applicability; `:117-142` uses non-freeze eligibility/computation years to calculate AIME and formula PIA; `:153-180` applies WEP/COLAs/totalization and MFB. | PIA; PIFC |
| Windfall elimination provision, wage-indexed and old-start | computed | `D/WageIndGeneral.cpp:60-82` computes coverage years, reduced first-factor PIA and half-pension guarantee; `D/oldstart.cpp:221-231` applies the lesser of half pension/half PIA reduction. `D/PiaMethod.cpp:493-503` gates WEP by eligibility, pension and benefit dates, excluding survivors and benefit dates on/after `amend118_273`; `D/piaparms.cpp:101` sets that cutoff to January 2024. | PIA; PIFC; downstream benefits. No separate WEP reduction field |
| Totalization PIA and attributed earnings | computed | `D/piacal.cpp:706-713,813-855` computes relative earnings position, attributes earnings and caps them; `D/PiaMethod.cpp:359-371` multiplies the PIA by US QCs divided by `4*N` and deconverts to eligibility. Called by `D/WageInd.cpp:151-156`, `D/oldstart.cpp:239-241`, `D/PiaTable.cpp:134-138`, and `D/WageIndNonFreeze.cpp:170-175`. | PIA; PIFC; downstream benefits. Totalization election is input |
| Disability freeze in PIA/computation years | computed | `D/piadata.cpp:941-987` derives freeze-year intervals from onset/cessation/FRA; `D/piacal.cpp:905-925` subtracts disability years from elapsed years. `D/WageIndGeneral.cpp:121-124,154-156`, `D/oldstart.cpp:139-141`, and `D/PiaTable.cpp:110-112` exclude wholly frozen earnings years. | PIA, MFB and downstream benefits; freeze years not individually printed |
| Wage-indexed retirement/survivor family maximum | computed | `D/WageInd.cpp:150-161` projects MFB bend points, splits eligibility PIA, evaluates MFB and applies COLAs; `D/PiaMethod.cpp:179-188,382-388` splits into four brackets and sums products. `D/percmfb.cpp:10` supplies 150%, 272%, 134%, 175%. | MFB |
| 1939 old-start family maximum | computed | `D/oldstart.cpp:292-303` computes 80% of old-start AMW, caps at $85 and twice PIA, and floors at $20. | MFB |
| 1950/1952/1954 old-start family maximum | computed | `D/oldstart.cpp:307-340` locates the PIB conversion-table index, retrieves `Pib50Mfb`, then uses `Pib52Mfb` or `Pib54Mfb` for the applicable benefit date. | MFB |
| Later old-start family maximum | computed | `D/oldstart.cpp:242-248` uses the wage-indexed MFB formula for the 1977 old-start branch; `:250-277` obtains old-table MFB otherwise. `D/oldpia.cpp:107-122,135-137,166-177` extends MFB and applies historical increases. | MFB |
| PIA-table / new-start family maximum | computed | `D/PiaTable.cpp:125-138` evaluates the historical table, saves `mfbsub`, and handles totalized table MFB; actual extension/COLA arithmetic is `D/oldpia.cpp:107-122,135-137,166-177`. | MFB |
| Transitional guarantee family maximum | computed | `D/TransGuar.cpp:113-121` computes the four-bracket MFB from transitional eligibility PIA and applies COLAs. | MFB |
| Special minimum family maximum | computed | `D/SpecMin.cpp:123-144` retrieves the date-specific special-minimum MFB, or uses old-table MFB for pre-1977 cases; `D/piaparms.cpp:735-740` initializes the modern table at 150% of special-minimum PIA. | MFB |
| Frozen minimum family maximum | computed | `D/FrozMin.cpp:106-107` starts with $122 PIA/$183 MFB, and `:83-84` increases MFB by the applicable COLAs. | MFB |
| Child-care dropout family maximum | computed | `D/ChildCareCalc.cpp:129-133` derives MFB brackets from the child-care PIA, sums them via `mfbCal`, and applies COLAs. Disability cases then receive the DI maximum override in `D/piacal.cpp:81-87`. | MFB |
| Disability guarantee family maximum | computed | `D/DibGuar.cpp:110-118` takes supplied cessation MFB, determines conversion, and applies COLAs; `:183-207` converts a DI maximum to the retirement/survivor formula when applicable using deconverted PIA and MFB brackets. | MFB |
| Non-freeze wage-indexed family maximum | computed | `D/WageIndNonFreeze.cpp:169-180` projects brackets using non-freeze eligibility and computes/increases MFB; `D/piacal.cpp:89-96` applies the non-freeze DI cap for disability cases. | MFB |
| Totalization family maximum | computed | `D/WageInd.cpp:151-161` prorates PIA, deconverts it, then computes MFB from the prorated eligibility PIA; analogous old-start branch `D/oldstart.cpp:239-248`; old-table totalized MFB `D/PiaTable.cpp:134-138` → `D/oldpia.cpp:198-218`. | MFB; this is not a separately printed unprorated MFB |
| Disability family maximum (1980 amendments) | computed | `D/PiaMethod.cpp:441-463` computes 85% of AIME, caps at 150% of PIA and floors at PIA; `:399-408` applies COLAs and floors again at payable-date PIA. `D/piacal.cpp:66-109` applies it for qualifying DI cases, including child-care/non-freeze candidates, before MFB selection. | MFB |
| Family maximum when reindexed widow PIA wins | computed | `D/piacal.cpp:205-221` substitutes reindexed widow full benefit but applies the ordinary worker MFB; `:322-330` keeps the wage-indexed MFB if a reindexed-widow PIA is the selected method. Reindexing does not create an independent larger widow MFB. | MFB; family full benefit/family benefit |
| Family-maximum allocation to auxiliary/survivor amounts | computed | `H/piacal.h:205-221` uses `(MFB-PIA)/auxiliary_total` in life cases and `MFB/survivor_total` in death cases. `D/piacal.cpp:1772-1790` clamps the ratio to [0,1], multiplies eligible full benefits, and leaves exempt BICs unreduced; invoked at `:217-221`. | family benefit; full benefit remains before allocation |
| Fully insured status | computed | `D/piacal.cpp:1914-1946` derives required QCs as elapsed years minus freeze years bounded to 6–40; `:2285-2329` compares earned QCs, with totalization/deemed/transitional branches. `:740-749` invokes and saves the result. | Combined insured only; native `piaData.finsCode.isFullyInsured()` is not a separate stock field |
| Currently insured status | computed | `D/piacal.cpp:2053-2065` accumulates QCs in a 13-quarter period; `:2300-2302,2318-2329` tests for at least 6 and distinguishes full/current combinations. `:1519-1527` performs the calculation on the batch path. | Combined insured only; currently-only survivor can print `T`; native `finsCode.isCurrentlyInsured()` is not separately emitted |
| Disability insured status (20/40, young-worker, blind, prior freeze) | computed | `D/piacal.cpp:758-762` invokes DI insured calculations; `:2561-2614` calculates QC requirements/actual QCs, retries young-worker and prior-freeze tests; `:2618-2649` combines full insured, 20/40, special and blindness conditions. | Combined insured becomes `F` for DI if `disInsCode.isDisabilityInsured()` is false (`B/anypiabdoc.cpp:265-267`); native DI code not separately printed |
| Worker early entitlement reduction | computed | `D/piacal.cpp:435-447,600-613` gets early months and AR factors (including prior OAB reduction for DI); `D/piaparms.cpp:948-972` implements months and piecewise monthly reduction; `D/piacal.cpp:143-158` multiplies PIA and rounds benefit. | worker benefit; age at benefit; no standalone reduction amount |
| Worker delayed retirement credits | computed | `D/piacal.cpp:587-595` finds first fully insured date and DRC months; `D/piaparms.cpp:1077-1079` computes `1 + months*retCredit`; `D/piacal.cpp:143-158` applies the factor. `:245-289,336-345` handles a special-minimum support PIA. | worker benefit; no standalone DRC amount |
| Aged spouse early entitlement reduction | computed | `D/piacal.cpp:486-497,676-683` computes spouse FRA, months, full factor and AR; `D/piaparms.cpp:982-998` implements piecewise monthly reduction. `D/piacal.cpp:223-235` applies age reduction after MFB and rounds. | family full benefit, family benefit |
| Aged/disabled widow(er) age limits and reductions | computed | `D/piacal.cpp:534-562` checks minimum/maximum entitlement ages and computes widow FRA; `:622-630,658-668` computes full and age-reduction factors; `:223-235` applies reductions. Arithmetic is in `D/piaparms.cpp:1095-1238` (disabled/aged widow month/factor branches). | family full benefit, family benefit; invalid age gives calculation error |
| Auxiliary amounts (spouse, child, child-in-care spouse) | computed | `D/piacal.cpp:483-518,647-650,676-683` chooses valid life BICs and factors; `:198-202` multiplies PIA by factor; `:217-235` applies MFB, age and dollar rounding. Category/qualifying relationship is supplied, not adjudicated. | family full benefit, family benefit; BIC |
| Survivor amounts (child, child-in-care parent, aged/disabled widow(er)) | computed | `D/piacal.cpp:521-568,637-640` chooses survivor factors; `:198-215` multiplies ordinary or higher reindexed PIA; `:217-235` applies survivor MFB, age reduction and rounding. | family full benefit, family benefit; BIC; PIFC |
| Widow(er)'s limit / RIB-LIM from deceased worker's reduced retirement benefit | not computed | `D/piaparms.cpp:1583-1596` contains correct-looking `min(widowBen,max(82.5%*PIA,oabBen))` arithmetic, but complete symbol search finds only declarations/definitions/wrappers, no caller. The actual terminal survivor path `D/piacal.cpp:198-235` ends after MFB, age and rounding, with no RIB-LIM call. **Inference from call-path inspection and whole-vendor search.** | None; family benefit must not be described as RIB-LIM-adjusted |
| Retirement earnings test / withholding | not computed | `D/RetireTest.cpp:57-91` contains exemption/fraction and months-withheld arithmetic, but complete symbol search for `earningsTestCal` finds only this definition and `H/RetireTest.h:36`. Neither the terminal worker path `D/piacal.cpp:138-158` nor family path `:198-235` calls it. **Inference from path inspection and whole-vendor search.** | None; benefits are before earnings-test withholding |
| Government pension offset (GPO) | not computed | `D/piaread.cpp:539-561` reads family BIC/birth/entitlement/onset, with no family pension; `H/Secondary.h:21-46` stores no pension/offset. Entire family amount path `D/piacal.cpp:198-235` only applies factor, reindexing, MFB, age and rounding. Noncovered worker pension is used for WEP (`D/WageIndGeneral.cpp:69-82`), not GPO. No GPO calculation symbol/branch found. **Inference from complete family data/path inspection and whole-vendor search.** | None; family benefit has no GPO subtraction (including historical dates) |
| Recomputations with later covered earnings | computed | `D/piadata.cpp:998-1003` includes earnings through year before requested benefit year (through death year for survivors); `D/WageInd.cpp:79-102` reorders/selects high years through that endpoint. `D/piacal.cpp:797-809` explicitly updates totalization AWI handling for AERO recomputations. A new run with later benefit date/earnings recalculates, rather than maintaining an award ledger. | PIA, MFB and benefit at requested benefit date; no annual change history |
| Cost-of-living increases after eligibility | computed | `D/PiaMethod.cpp:243-300` loops eligibility through the last increase month at requested benefit date, applying annual increases/rounding and the special 1999 adjustment; invoked for PIA/MFB in `D/WageInd.cpp:137-161`. Historical table COLAs use `D/oldpia.cpp:166-187`; special minimum uses `D/SpecMin.cpp:127-135`. | PIA, MFB and downstream benefits at benefit date |
| Medical disability decision, onset, waiting-period and cessation dates | input only | `D/piaread.cpp:454-487,499-525` parses supplied disability periods and sets onset, waiting-period/entitlement and cessation dates, then validates them. `D/piadata.cpp:948-987` consumes those dates for freeze arithmetic. This is not a medical/SGA adjudication from employment/health facts. | No decision field; dates influence PIA/DI eligibility checks |
| Qualifying family relationship / beneficiary category | input only | `D/piaread.cpp:539-561` takes the BIC and entitlement date directly from the family record; `D/piacal.cpp:483-571` dispatches formulas/age checks by that BIC. Marriage/divorce duration, dependency evidence and qualifying child-care facts are not determined from a relationship history. | BIC; benefit conditioned on supplied category |
| Prior disability award PIA/MFB at cessation | input only | `D/piaread.cpp:480-487,519-525` copies supplied cessation PIA/MFB into prior periods. `D/DibGuar.cpp:106-118` uses those supplied amounts to calculate the guarantee/conversion/COLAs. | No separately emitted prior amount; can influence selected PIA/MFB |

The coverage totals count rows, not independent statutory provisions; formula
components and method-specific family maxima are deliberately separate rows.
They describe this archive and console path. They should not be read as a
current-law certification or as proof that the generated test set reaches all
historical branches.

To reproduce the negative findings without relying on function names alone,
read the terminal amount assignments at `D/piacal.cpp:138-158,198-235` and run:

```sh
rg -n 'earningsTestCal|ribLimCal|government pension|Government Pension|\bGPO\b' \
  anypia/vendor/oactobjs32 anypia/vendor/anypiab
```

The RIB-LIM matches are declarations/definitions/wrappers; the earnings-test
matches are declaration/definition only. GPO text appears in commented-out
Statement explanatory material, not benefit arithmetic. This search is
supporting evidence; the amount-path read is what establishes the conclusion.
