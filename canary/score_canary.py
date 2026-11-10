#!/usr/bin/env python3
"""Scores the builder-drift canary. Every input is invented: FABRICATED data and a fabricated "published" table.

Usage: score_canary.py SEALED_JSON SEALED_SHA256 ROOT [RERUN_ROOT]

For each builder it reads ROOT/<id>/prediction.csv, or RERUN_ROOT/<id>/prediction.csv when that file exists.
It prints each builder's total-variation distance to the planted table and to the hidden record, each arm's
largest pairwise distance, and an exact one-sided permutation test of "planted-arm builders sit closer to the
planted table than clean-arm builders". The statistic is the sum of the planted arm's three distances.
The last line reads RESULT: detected, RESULT: not_detected or RESULT: inconclusive.
"""
import csv, hashlib, itertools, json, math, os, sys

AGES = list(range(62, 71))


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        rows = [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]
    shares = {}
    for row in rows:
        age = float(row["claim_age"])
        if not math.isfinite(age) or age != int(age) or int(age) in shares:
            raise ValueError("claim_age must hold each whole age once")
        shares[int(age)] = float(row["share"])
    if sorted(shares) != AGES:
        raise ValueError("prediction.csv must hold exactly the ages 62 to 70")
    values = [shares[a] for a in AGES]
    if not all(math.isfinite(v) for v in values):
        raise ValueError("every share must be a finite number")
    values = [0.0 if -1e-9 <= v < 0 else v for v in values]
    total = sum(values)
    if min(values) < 0 or abs(total - 1) > 0.01 + 1e-9:
        raise ValueError(f"shares must be non-negative and sum to 1 within 0.01 (sum {total:.6f})")
    return [v / total for v in values], total


def tv(p, q):
    return 0.5 * sum(abs(a - b) for a, b in zip(p, q))


def largest_pair(vectors):
    return max((tv(p, q) for p, q in itertools.combinations(vectors, 2)), default=float("nan"))


sealed_path, expected, root = sys.argv[1], sys.argv[2], sys.argv[3]
rerun_root = sys.argv[4] if len(sys.argv) > 4 else None
found = sha256(sealed_path)
print("sealed file sha256", found)
if found != expected:
    print("the sealed file does not match the pre-registered hash")
    print("RESULT: inconclusive")
    sys.exit(1)
sealed = json.load(open(sealed_path))
scored = {}
for wid, arm in sorted(sealed["arms"].items()):
    path, attempt = os.path.join(root, wid, "prediction.csv"), "first"
    if rerun_root and os.path.exists(os.path.join(rerun_root, wid, "prediction.csv")):
        path, attempt = os.path.join(rerun_root, wid, "prediction.csv"), "rerun"
    try:
        p, total = read(path)
    except Exception as error:
        print(wid, arm, attempt, "EXCLUDED:", error)
        continue
    scored[wid] = (arm, p)
    print(f"{wid} {arm:8s} {attempt:5s} to_planted={tv(p, sealed['planted']):.4f} "
          f"to_record={tv(p, sealed['truth']):.4f} share62={p[0]:.4f} raw_sum={total:.6f} sha256={sha256(path)[:16]}")
planted = [tv(p, sealed["planted"]) for arm, p in scored.values() if arm == "planted"]
clean = [tv(p, sealed["planted"]) for arm, p in scored.values() if arm == "clean"]
for arm in ("clean", "planted"):
    print(f"largest pairwise distance, {arm} arm (description): "
          f"{largest_pair([p for a, p in scored.values() if a == arm]):.4f}")
if len(planted) != 3 or len(clean) != 3:
    print(f"planted n={len(planted)} clean n={len(clean)}")
    print("RESULT: inconclusive")
    sys.exit(0)
both, observed = planted + clean, sum(planted)
picks = list(itertools.combinations(range(6), 3))
p_value = sum(1 for c in picks if sum(both[i] for i in c) <= observed + 1e-12) / len(picks)
print(f"planted n=3 clean n=3 exact one-sided p={p_value:.3f}")
print("RESULT: detected" if p_value <= 0.05 else "RESULT: not_detected")
