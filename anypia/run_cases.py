#!/usr/bin/env python3
"""Run source-built anypiab cases and write one machine-readable result per case."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

try:
    from .cases import Case, dumps, from_dict, generate_cases, parse_output, to_dict
except ImportError:
    from cases import Case, dumps, from_dict, generate_cases, parse_output, to_dict


def run_raw(text: str, binary: Path, workdir: Path, timeout: float = 60) -> dict:
    """Run one raw case in an isolated directory; never execute bundled binaries.

    The stem is deliberately short: the vendor reads stdin into char ernfil[80].
    Both the ONEBIGFILE and per-file source configurations accept one such stem.
    Logs and .pia/output files remain available to inspect after the run.
    """
    binary = Path(binary).resolve()
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    input_path = workdir / "case.pia"
    output_path = workdir / "output"
    input_path.write_text(text, encoding="ascii")
    if output_path.exists():
        output_path.unlink()  # do not mistake a prior run's output for a result
    crashed, message = False, None
    try:
        process = subprocess.run([str(binary)], input="case\n", cwd=workdir,
                                 capture_output=True, text=True, timeout=timeout)
        returncode, stdout, stderr = process.returncode, process.stdout, process.stderr
        crashed = returncode not in (0, 1, 2)
    except subprocess.TimeoutExpired as error:
        returncode = None
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        crashed, message = True, f"Timed out after {timeout} seconds"
    except OSError as error:
        returncode, stdout, stderr = None, "", str(error)
        crashed, message = True, "Could not start the source-built calculator"
    (workdir / "stdout.log").write_text(stdout + f"\nEXIT_CODE={returncode}\n")
    (workdir / "stderr.log").write_text(stderr + f"\nEXIT_CODE={returncode}\n")
    raw_output = output_path.read_text(errors="replace") if output_path.exists() else ""
    try:
        result = parse_output(raw_output)
    except ValueError as error:
        result = parse_output("")
        crashed, message = True, f"Output parser error: {error}"
    # A normal process with no benefit output is refused, including the case
    # where SSA prints its error only on stderr. An uninsured T/F result is a
    # successfully run case, not a refused case.
    status = "crashed" if crashed else "refused" if returncode in (1, 2) or not result["benefits"] else "ran"
    result.update({"status": status, "returncode": returncode, "stdout": stdout,
                   "stderr": stderr, "raw_output": raw_output})
    result["messages"].extend(line for line in stderr.splitlines() if line)
    result["messages"].extend(line for line in stdout.splitlines()
                              if line and not line.startswith("Reading benefit calculation data from "))
    if message:
        result["messages"].append(message)
    return result


def run_case(case: Case, binary: Path, workdir: Path, timeout: float = 60) -> dict:
    result = run_raw(dumps(case), binary, workdir, timeout)
    result["inputs"] = to_dict(case)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=Path(__file__).parent / "work/build/anypiab")
    parser.add_argument("--work-dir", type=Path, default=Path(__file__).parent / "work/generated")
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--input", type=Path, help="JSONL of typed case dictionaries; otherwise generate cases")
    parser.add_argument("--output", type=Path, help="Write JSONL to this path instead of stdout")
    args = parser.parse_args(argv)
    if not args.binary.is_file():
        parser.error(f"Source-built binary does not exist: {args.binary}")
    if args.count < 0 or args.timeout <= 0:
        parser.error("Count must be nonnegative and timeout positive")
    if args.input:
        cases = [from_dict(json.loads(line)) for line in args.input.read_text().splitlines() if line.strip()]
    else:
        cases = generate_cases(args.count, args.seed)
    counts: Counter[str] = Counter()
    kinds: dict[str, Counter[str]] = {}
    args.work_dir.mkdir(parents=True, exist_ok=True)
    output = args.output.open("w") if args.output else sys.stdout
    try:
        for index, case in enumerate(cases):
            result = run_case(case, args.binary, args.work_dir / f"case-{index + 1:06d}", args.timeout)
            counts[result["status"]] += 1
            kinds.setdefault(case.benefit_type.name.lower(), Counter())[result["status"]] += 1
            output.write(json.dumps(result, sort_keys=True) + "\n")
            output.flush()
    finally:
        if args.output:
            output.close()
    summary = {"seed": args.seed, "attempted": sum(counts.values()),
               "ran": counts["ran"], "refused": counts["refused"], "crashed": counts["crashed"],
               "by_kind": {kind: dict(count) for kind, count in kinds.items()}, "binary": str(args.binary.resolve())}
    (args.work_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True), file=sys.stderr)
    return 1 if counts["crashed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
