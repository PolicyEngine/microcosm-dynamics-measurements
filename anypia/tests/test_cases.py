"""Properties exercise variable-width histories, optional dates, and families."""

from datetime import date
from decimal import Decimal
from pathlib import Path
import sys

import pytest
from hypothesis import given, settings, strategies as st


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cases import (BenefitType, Case, DisabilityPeriod, FamilyMember, Month,
                   dumps, dumps_many, from_dict, generate_cases, loads,
                   loads_many, parse_output, to_dict)


@st.composite
def typed_cases(draw):
    kind = draw(st.sampled_from(list(BenefitType)))
    birth = draw(st.dates(min_value=date(1940, 1, 1), max_value=date(1980, 12, 31)))
    first = draw(st.integers(1978, 2000))
    length = draw(st.integers(1, 50))
    cents = draw(st.lists(st.integers(0, 99999999), min_size=length, max_size=length))
    earnings = {first + offset: Decimal(value) / 100 for offset, value in enumerate(cents)}
    month = draw(st.integers(1, 12))
    entitlement = Month(2024, month)
    benefit = draw(st.one_of(st.none(), st.just(entitlement.add(5))))
    disability = ()
    death = None
    family = ()
    if kind == BenefitType.DISABILITY:
        onset = date(2023, 1, 15)
        disability = (DisabilityPeriod(onset, entitlement, Month(2023, 2)),)
    if draw(st.booleans()):
        disability = (DisabilityPeriod(date(2000, 2, 3), Month(2000, 8), Month(2000, 3), Month(2003, 3), Decimal("800.10"), Decimal("1200.50")),) + disability
        disability = disability[::-1]
    if kind == BenefitType.SURVIVOR:
        death = date(2023, 12, 15)
        benefit = Month(2024, month)
        entitlement = None
        member = FamilyMember(draw(st.sampled_from(["C1", "D ", "D6", "E "])), date(1950, 2, 3), benefit)
        family = (member,)
    elif draw(st.booleans()):
        family = (FamilyMember("B ", date(1950, 2, 3), entitlement), FamilyMember("C1", date(2010, 10, 1), entitlement))
    extras = ("131", "140", "95200 20") if draw(st.booleans()) else ()
    return Case(draw(st.integers(1, 999999999)).__format__("09d"), birth,
                draw(st.sampled_from(["male", "female"])), kind, entitlement,
                earnings, benefit, death, disability, family, "Property case", extras)


@settings(max_examples=150, deadline=None)
@given(typed_cases())
def test_wire_and_json_round_trip(case):
    restored = loads(dumps(case))
    assert restored == case
    assert from_dict(to_dict(case)) == case
    assert dumps(restored) == dumps(case)


@settings(max_examples=35, deadline=None)
@given(st.lists(typed_cases(), min_size=1, max_size=6))
def test_multiple_case_record_boundaries(cases):
    assert loads_many(dumps_many(cases)) == cases


@given(st.integers(0, 100000))
def test_seed_reproduces_three_family_types(seed):
    left = list(generate_cases(9, seed))
    assert left == list(generate_cases(9, seed))
    assert {case.benefit_type for case in left} == set(BenefitType)
    assert all(loads(dumps(case)) == case for case in left)
    assert all(case.death_date is not None and case.family for case in left if case.benefit_type == BenefitType.SURVIVOR)


def test_sparse_earnings_become_explicit_zero():
    case = next(generate_cases(1))
    values = to_dict(case)
    values["earnings"] = {"2000": "100.00", "2002": "200.00"}
    sparse = from_dict(values)
    assert sparse.earnings[2001] == 0
    assert loads(dumps(sparse)) == sparse


@pytest.mark.parametrize("mutation", [lambda text: "\n".join("99" + line[2:] if line.startswith("22") else line for line in text.splitlines()) + "\n", lambda text: text + text.splitlines()[0] + "\n", lambda text: "\n".join("07" + line[2:] if line.startswith("06") else line for line in text.splitlines()) + "\n"])
def test_malformed_records_fail(mutation):
    with pytest.raises(ValueError):
        loads(mutation(dumps(next(generate_cases(1)))))


def test_output_worker_and_spaced_bic_are_parsed_without_losing_cents():
    primary = "001-23-4567 01/02/1950" + f"{Decimal('1234.50'):8.2f}{Decimal('1851.70'):8.2f}{Decimal('930'):8.2f}" + "  62 and  1 month  A T"
    member = "001-23-4567 02/03/1950" + f"{Decimal('1234.50'):8.2f}{Decimal('1851.70'):8.2f}{Decimal('617.20'):8.2f}{Decimal('432'):8.2f}" + " A B  T"
    result = parse_output(primary + "\n" + member + "\nNeed annual pre-1951 earnings in prior case\n")
    assert result["primary_insurance_amount"] == "1234.50"
    assert result["maximum_family_benefit"] == "1851.70"
    assert result["benefits"][0]["age_months"] == 1
    assert result["benefits"][1]["bic"] == "B "
    assert result["benefits"][1]["full_benefit"] == "617.20"
    assert result["insured_status"] == {"combined": True, "fully": None, "currently": None, "disability": None}
    assert result["messages"] == ["Need annual pre-1951 earnings in prior case"]


def test_output_adjacent_large_money_fields_and_uninsured():
    line = "000-00-0001 12/03/1950" + "10000.0015000.00 9999.00" + "  70 and  0 months A F"
    result = parse_output(line)
    assert result["primary_insurance_amount"] == "10000.00"
    assert result["insured_status"]["combined"] is False


def test_output_malformed_numeric_row_fails():
    with pytest.raises(ValueError):
        parse_output("000-00-0001 12/03/1950 invalid result")


def test_codec_rejects_fields_that_cannot_survive_the_wire_format():
    with pytest.raises(ValueError, match="cessation amounts require"):
        DisabilityPeriod(date(2000, 1, 1), Month(2000, 6), Month(2000, 1), cessation_pia=Decimal(1))
    with pytest.raises(ValueError, match="BIC"):
        FamilyMember("B\n", date(1950, 1, 1), Month(2020, 1))
    values = to_dict(next(generate_cases(1)))
    values["extra_records"] = ["131", "130"]
    with pytest.raises(ValueError, match="unique"):
        from_dict(values)
    values["extra_records"] = []
    values["ssn"] = "١٢٣٤٥٦٧٨٩"
    with pytest.raises(ValueError, match="nine-digit"):
        from_dict(values)


def test_codec_rejects_unpaired_disability_or_surplus_earnings_rows():
    text = dumps(list(generate_cases(2))[1])
    text = "\n".join("10" + line[2:] if line.startswith("09") else line for line in text.splitlines()) + "\n"
    with pytest.raises(ValueError, match="requires record 09"):
        loads(text)
    rows = dumps(next(generate_cases(1))).splitlines() + ["29       1.00"]
    text = "\n".join(sorted(rows, key=lambda row: int(row[:2]))) + "\n"
    with pytest.raises(ValueError, match="declared year span"):
        loads(text)


def test_codec_rejects_order_that_changes_vendor_date_semantics():
    rows = dumps(next(generate_cases(1))).splitlines()
    rows.insert(1, "04012024")  # before 03: vendor 03 would overwrite this month
    with pytest.raises(ValueError, match="increasing"):
        loads("\n".join(rows) + "\n")


@pytest.mark.parametrize("returncode, expected", [(1, "refused"), (2, "refused"), (3, "crashed"), (-11, "crashed")])
def test_runner_distinguishes_ssa_errors_from_unexpected_exits(monkeypatch, tmp_path, returncode, expected):
    import subprocess
    import run_cases

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], returncode, "", "Calculator diagnostic\n")

    monkeypatch.setattr(run_cases.subprocess, "run", fake_run)
    result = run_cases.run_raw(dumps(next(generate_cases(1))), ROOT / "work/build/anypiab", tmp_path)
    assert result["status"] == expected
    assert result["returncode"] == returncode
    assert "Calculator diagnostic" in result["messages"]


@pytest.mark.skipif(not (ROOT / "work/build/anypiab").exists(), reason="Build source first")
def test_three_generated_case_types_reach_calculator(tmp_path):
    from run_cases import run_case
    for index, case in enumerate(generate_cases(3, 55)):
        result = run_case(case, ROOT / "work/build/anypiab", tmp_path / str(index))
        assert result["status"] == "ran", result
        assert result["benefits"]
        assert all(row["ssn"] == case.ssn for row in result["benefits"])
