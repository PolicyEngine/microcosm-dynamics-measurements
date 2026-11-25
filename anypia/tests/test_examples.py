"""Compare SSA's shipped examples to the guide, without adopting actuals as goldens.

The baseline is the separately downloaded guide, not a saved run of the port.
SSA's input archive and guide say 2026; the pinned source has base year 2025.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

ANYPIA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ANYPIA.parent))
from anypia.cases import parse_output

FIXTURES = Path(__file__).parent / "fixtures"
GUIDE = json.loads((FIXTURES / "guide-examples.json").read_text())
BINARY = Path(os.environ.get("ANYPIA_BINARY", str(ANYPIA / "work/build/anypiab"))).resolve()
SOURCE_BINARY = Path(os.environ.get("ANYPIA_SOURCE_BINARY", str(BINARY.with_name("anypiatest")))).resolve()
WORK = ANYPIA / "work/examples"


def split_examples(text: str) -> dict[int, str]:
    """The first two columns hold record type; 01 starts each worker."""
    cases = re.split(r"(?m)(?=^01)", text)
    result = {}
    for case in cases:
        if not case.strip():
            continue
        name = re.search(r"^16Sample (\d+)\s*$", case, re.MULTILINE | re.IGNORECASE)
        if not name:
            raise ValueError("SSA example is missing its Sample number")
        number = int(name[1])
        if number in result:
            raise ValueError(f"Duplicate SSA example {number}")
        result[number] = case.rstrip() + "\n"
    return result


INPUTS = split_examples((FIXTURES / "batch-examples.pia").read_text())


def observed_amounts(parsed: dict, details: str) -> dict[str, str | list[str]]:
    """Map guide labels only to fields actually emitted by the SSA program."""
    amounts = {}
    if parsed["primary_insurance_amount"] is not None:
        amounts["PIA"] = parsed["primary_insurance_amount"]
        amounts["regular PIA"] = parsed["primary_insurance_amount"]
        amounts["MFB"] = parsed["maximum_family_benefit"]
    benefits = parsed["benefits"]
    if len(benefits) == 1:
        amounts["MBA"] = benefits[0]["benefit"]
    selected_widow = [row for row in benefits if row["method"] == "W" and row["bic"][0] in "DW"]
    if len(selected_widow) == 1:
        # These post-1973 widow samples have benefit factor 1.0. The source
        # assigns reindexed piaEnt to fullBenefit when method W wins:
        # piadata/piacal.cpp:205-214; piaparms.cpp:1198-1240.
        amounts["re-indexed widow(er) guarantee PIA"] = selected_widow[0]["full_benefit"]
    for title, field in (
        ("Re-indexed Widow (1983 Act)", "re-indexed widow(er) guarantee PIA"),
        ("Child-Care Dropout Year Method", "childcare dropout year PIA"),
    ):
        match = re.search(re.escape(title) + r" PIA:\s*([\d,.]+)", details)
        if match:
            amounts[field] = match[1].replace(",", "")
    if "childcare dropout year PIA" in amounts:
        # Summary highPia is the selected childcare method, not the ordinary
        # wage-indexed method. SSA's one-page report omits the latter amount.
        amounts.pop("regular PIA", None)
    elif any(row["method"] == "Y" for row in benefits):
        amounts["childcare dropout year PIA"] = parsed["primary_insurance_amount"]
        amounts.pop("regular PIA", None)
    widows = [row["benefit"] for row in benefits if row["bic"].startswith("W")]
    children = [row["benefit"] for row in benefits if row["bic"].startswith("C")]
    if len(widows) == 1:
        amounts["disabled widow MBA"] = widows[0]
    if children:
        amounts["child MBA (two)"] = children
    return amounts


def execute_example(number: int) -> dict:
    directory = WORK / f"sample-{number:02d}"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "case.pia").write_text(INPUTS[number])
    process = subprocess.run([str(BINARY)], input="case.pia\n", text=True,
                             cwd=directory, capture_output=True, timeout=120)
    (directory / "stdout.log").write_text(process.stdout)
    (directory / "stderr.log").write_text(process.stderr + f"\nEXIT_CODE={process.returncode}\n")
    output = (directory / "output").read_text() if (directory / "output").exists() else ""
    details = (directory / "details.out").read_text() if (directory / "details.out").exists() else ""
    parsed = parse_output(output)
    example = next(item for item in GUIDE if item["number"] == number)
    observed = observed_amounts(parsed, details)
    missing, different = [], {}
    for field, expected in example["expected"].items():
        if field not in observed:
            missing.append(field)
            continue
        actual = observed[field]
        values = actual if isinstance(actual, list) else [actual]
        if any(value != expected for value in values):
            different[field] = {"expected": expected, "actual": actual}
    result = {"number": number, "guide_pdf_page": example["pdf_page"],
              "guide_computation_year": example["computation_year"],
              "source_computation_year": 2025, "returncode": process.returncode,
              "expected": example["expected"], "observed": observed,
              "missing_output_fields": missing, "different": different,
              "calculator_messages": parsed["messages"],
              "reproduced": process.returncode == 0 and not different and not missing,
              "input_has_2026_assumptions": any(line.startswith("402026") for line in INPUTS[number].splitlines())}
    (directory / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def test_example_inventory():
    assert len(GUIDE) == 30
    assert set(INPUTS) == {item["number"] for item in GUIDE} == set(range(1, 31))
    assert all(item["computation_year"] == 2026 and item["expected"] for item in GUIDE)


@pytest.mark.parametrize("number", range(1, 31), ids=lambda number: f"ssa-sample-{number}")
def test_documented_example(number):
    if not BINARY.is_file():
        pytest.skip("Build source with anypia/build.sh before executing SSA examples")
    result = execute_example(number)
    assert result["returncode"] == 0, result
    if result["different"] and result["input_has_2026_assumptions"]:
        pytest.xfail("Guide/input use 2026; pinned source uses 2025: " + json.dumps(result["different"]))
    assert not result["different"], result
    if result["missing_output_fields"]:
        pytest.xfail("SSA's enabled output does not expose " + ", ".join(result["missing_output_fields"]))


def test_embedded_source_example():
    binary = SOURCE_BINARY if SOURCE_BINARY.is_file() else BINARY
    if not binary.is_file():
        pytest.skip("Build source with anypia/build.sh before executing SSA examples")
    directory = WORK / "embedded-source-sample"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "case.pia").write_text((FIXTURES / "embedded-source-sample.pia").read_text())
    process = subprocess.run([str(binary)], input="" if binary == SOURCE_BINARY else "case.pia\n", text=True,
                             cwd=directory, capture_output=True, timeout=120)
    (directory / "stdout.log").write_text(process.stdout)
    (directory / "stderr.log").write_text(process.stderr + f"\nEXIT_CODE={process.returncode}\n")
    parsed = parse_output((directory / "output").read_text())
    report = {"returncode": process.returncode, "documented_numeric_baseline": None,
              "source": "vendor/anypiab/anypiatestdoc.cpp:133-157",
              "execution": "native embedded sample" if binary == SOURCE_BINARY else "batch input translated from source assignments",
              "observed": parsed}
    (directory / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    assert process.returncode == 0, report
    assert len(parsed["benefits"]) == 1 and parsed["primary_insurance_amount"] is not None
