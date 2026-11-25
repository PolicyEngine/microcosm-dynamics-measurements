"""Summarize comparisons already executed by test_examples.py."""
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    work = Path(__file__).resolve().parents[1] / "work"
    results = [json.loads((work / "examples" / f"sample-{number:02d}" / "comparison.json").read_text())
               for number in range(1, 31)]
    embedded = json.loads((work / "examples/embedded-source-sample/comparison.json").read_text())
    summary = {
        "all_distinct_examples": 31,
        "all_distinct_examples_ran": len(results) + 1,
        "guide_examples": 30,
        "ran": len(results),
        "refused": sum(result["returncode"] > 0 for result in results),
        "crashed": sum(result["returncode"] < 0 for result in results),
        "reproduced_all_documented_fields": sum(result["reproduced"] for result in results),
        "matched_all_emitted_fields": sum(result["returncode"] == 0 and not result["different"] for result in results),
        "different": sum(bool(result["different"]) for result in results),
        "missing_output_fields": sum(bool(result["missing_output_fields"]) for result in results),
        "source_computation_year": 2025,
        "guide_computation_year": 2026,
        "embedded_source_example": embedded,
        "results": results,
    }
    (work / "example-results.json").write_text(json.dumps(summary, indent=2) + "\n")
    table = ["| Guide sample | Result | Differences / unavailable fields |",
             "|---|---|---|"]
    for result in results:
        if result["reproduced"]:
            state = "All documented fields reproduced"
        elif result["different"]:
            state = "Documented output differs"
        elif result["returncode"]:
            state = f"Calculator exit {result['returncode']}"
        else:
            state = "All emitted fields match; partial comparison"
        notes = [f"{field}: expected {amounts['expected']}, observed {amounts['actual']}"
                 for field, amounts in result["different"].items()]
        notes.extend(f"not emitted: {field}" for field in result["missing_output_fields"])
        table.append(f"| {result['number']} (PDF p. {result['guide_pdf_page']}) | {state} | {'; '.join(notes) or '—'} |")
    (work / "example-results-table.md").write_text("\n".join(table) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key not in {"results", "embedded_source_example"}}, indent=2))


if __name__ == "__main__":
    main()
