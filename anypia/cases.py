"""Typed, lossless core of SSA Detailed Calculator's fixed-width .pia format.

Only the standard library is used. See FORMAT.md for the supported subset,
source references, and the distinction between combined and granular insurance.
Money is Decimal; JSON represents money as decimal strings, never binary floats.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import IntEnum
import random
import re
from typing import Iterable


class BenefitType(IntEnum):
    RETIREMENT = 1
    SURVIVOR = 2
    DISABILITY = 3


@dataclass(frozen=True, order=True)
class Month:
    year: int
    month: int

    def __post_init__(self) -> None:
        date(self.year, self.month, 1)

    def add(self, months: int) -> Month:
        year, month = divmod(self.year * 12 + self.month - 1 + months, 12)
        return Month(year, month + 1)

    def wire(self) -> str:
        return f"{self.month:02d}{self.year:04d}"

    def iso(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    @classmethod
    def parse(cls, text: str) -> Month:
        if not re.fullmatch(r"[0-9]{6}", text):
            raise ValueError(f"Expected MMYYYY, got {text!r}")
        return cls(int(text[2:]), int(text[:2]))

    @classmethod
    def from_iso(cls, text: str) -> Month:
        year, month = text.split("-")
        return cls(int(year), int(month))


def money(value: Decimal | str | int) -> Decimal:
    amount = Decimal(value)
    if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal(".01")):
        raise ValueError(f"Expected nonnegative money with at most two decimals: {value!r}")
    return amount.quantize(Decimal(".01"))


def _date_wire(value: date) -> str:
    return f"{value.month:02d}{value.day:02d}{value.year:04d}"


def _parse_date(text: str) -> date:
    if not re.fullmatch(r"[0-9]{8}", text):
        raise ValueError(f"Expected MMDDYYYY, got {text!r}")
    return date(int(text[4:]), int(text[:2]), int(text[2:4]))


@dataclass(frozen=True)
class DisabilityPeriod:
    onset: date
    entitlement: Month
    waiting: Month
    cessation: Month | None = None
    cessation_pia: Decimal = Decimal("0.00")
    cessation_mfb: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        object.__setattr__(self, "cessation_pia", money(self.cessation_pia))
        object.__setattr__(self, "cessation_mfb", money(self.cessation_mfb))
        if any(len(f"{amount:.2f}") > 10 for amount in (self.cessation_pia, self.cessation_mfb)):
            raise ValueError("Disability cessation amount exceeds ten columns")
        if self.cessation is None and (self.cessation_pia or self.cessation_mfb):
            raise ValueError("Disability cessation amounts require a cessation month")


@dataclass(frozen=True)
class FamilyMember:
    bic: str
    birth_date: date
    entitlement: Month
    onset: date | None = None

    def __post_init__(self) -> None:
        bic = self.bic.ljust(2)
        if len(bic) != 2 or bic[0] not in "BCDEW" or not bic[1].isascii() or not bic[1].isprintable():
            raise ValueError("BIC must be a two-character life/survivor beneficiary code")
        if bic[0] == "W" and self.onset is None:
            raise ValueError("Disabled widow(er) BIC W requires an onset date")
        if bic[0] != "W" and self.onset is not None:
            raise ValueError("Family-member onset is stored only for BIC W")
        object.__setattr__(self, "bic", bic)


@dataclass(frozen=True)
class Case:
    ssn: str
    birth_date: date
    sex: str
    benefit_type: BenefitType
    entitlement: Month | None
    earnings: dict[int, Decimal]
    benefit_date: Month | None = None
    death_date: date | None = None
    disability: tuple[DisabilityPeriod, ...] = ()
    family: tuple[FamilyMember, ...] = ()
    name: str = ""
    extra_records: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9]{9}", self.ssn):
            raise ValueError("Use a nine-digit synthetic SSN identifier")
        if self.sex not in ("male", "female"):
            raise ValueError("SSA's format supports male/female worker sex")
        kind = BenefitType(self.benefit_type)
        object.__setattr__(self, "benefit_type", kind)
        if kind == BenefitType.SURVIVOR:
            if self.entitlement is not None:
                raise ValueError("SSA ignores worker entitlement for survivors; use family entitlements")
            if self.death_date is None or self.benefit_date is None or not self.family:
                raise ValueError("Survivor requires death date, benefit month, and family")
        elif self.entitlement is None:
            raise ValueError("Retirement/disability requires worker entitlement")
        if kind == BenefitType.DISABILITY and not self.disability:
            raise ValueError("Disability requires a disability period")
        if len(self.disability) > 2 or len(self.family) > 15:
            raise ValueError("SSA supports two disability periods and fifteen family members")
        if any(period.cessation is None and (kind != BenefitType.DISABILITY or index)
               for index, period in enumerate(self.disability)):
            raise ValueError("A prior disability period requires cessation")
        if not self.earnings:
            raise ValueError("Supply at least one earnings year, including zero if appropriate")
        first, last = min(self.earnings), max(self.earnings)
        if first < 1937 or last > 2100 or last - first >= 80:
            raise ValueError("Earnings must be an at-most-80-year span within 1937..2100")
        # Missing interior years are explicitly zero; this is canonical in .pia.
        earnings = {year: money(self.earnings.get(year, 0)) for year in range(first, last + 1)}
        if any(len(f"{amount:.2f}") > 11 for amount in earnings.values()):
            raise ValueError("Earnings exceed the source's eleven-column field")
        object.__setattr__(self, "earnings", earnings)
        if "\n" in self.name or "\r" in self.name:
            raise ValueError("Name must fit one record")
        if self.name and not self.name.isascii():
            raise ValueError("Use ASCII names in the calculator's legacy file format")
        seen_extra: set[int] = set()
        for line in self.extra_records:
            if len(line) < 2 or not line.isascii() or not line[:2].isdigit() or "\n" in line or "\r" in line:
                raise ValueError("Extra records must include a two-digit type and no newline")
            number = int(line[:2])
            if number in seen_extra:
                raise ValueError("Extra record types must be unique")
            seen_extra.add(number)
            if number in {1, 2, 3, 4, 6, 9, 10, 16} or 22 <= number <= 29 or 69 <= number <= 83:
                raise ValueError("Extra record duplicates a typed field")
            if number in {7, 8}:
                raise ValueError("Projected earnings are outside the typed subset; use a raw .pia file")
            if not 5 <= number <= 97:
                raise ValueError("Extra record number is outside the vendor format")
        object.__setattr__(self, "extra_records", tuple(sorted(self.extra_records, key=lambda line: int(line[:2]))))


def dumps(case: Case) -> str:
    """Serialize one case. Every record ends in a newline, including the last."""
    records = [f"01{case.ssn}{int(case.sex == 'female')}{_date_wire(case.birth_date)}"]
    if case.death_date:
        records.append("02" + _date_wire(case.death_date))
    records.append(f"03{int(case.benefit_type)}" + (case.entitlement.wire() if case.entitlement else ""))
    if case.benefit_date:
        records.append("04" + case.benefit_date.wire())
    first, last = min(case.earnings), max(case.earnings)
    records.append(f"06{first:04d}{last:04d}")
    for index, period in enumerate(case.disability):
        row = f"{9 + index:02d}" + _date_wire(period.onset) + period.entitlement.wire() + period.waiting.wire()
        if period.cessation:
            row += period.cessation.wire() + f"{period.cessation_pia:10.2f}{period.cessation_mfb:10.2f}"
        elif case.benefit_type != BenefitType.DISABILITY or index:
            raise ValueError("A prior disability period requires cessation")
        records.append(row)
    if case.name:
        records.append("16" + case.name)
    for index, start in enumerate(range(first, last + 1, 10)):
        records.append(f"{22 + index:02d}" + "".join(f"{case.earnings[year]:11.2f}" for year in range(start, min(start + 10, last + 1))))
    for index, member in enumerate(case.family):
        records.append(f"{69 + index:02d}{member.bic}" + _date_wire(member.birth_date) + member.entitlement.wire() + (_date_wire(member.onset) if member.onset else ""))
    records.extend(case.extra_records)
    records.sort(key=lambda line: int(line[:2]))
    return "\n".join(records) + "\n"


def loads(text: str) -> Case:
    """Parse one case in the typed subset; preserve other records verbatim.

    Unsupported projection records fail explicitly rather than silently changing
    which years an earnings row represents. Multi-case files use loads_many.
    """
    lines = text.splitlines()
    if not lines or not lines[0].startswith("01") or any(not line for line in lines):
        raise ValueError("A case must start with record 01 and contain no blank records")
    values: dict[int, str] = {}
    extra: list[str] = []
    previous_number = 0
    for line in lines:
        if len(line) < 2 or not line.isascii() or not line[:2].isdigit():
            raise ValueError(f"Invalid record: {line!r}")
        number = int(line[:2])
        if number in values:
            raise ValueError(f"Duplicate record {number:02d}")
        if number < previous_number:
            raise ValueError("Typed adapter requires increasing record-number order")
        previous_number = number
        values[number] = line[2:]
        if number not in {1, 2, 3, 4, 6, 9, 10, 16} and not 22 <= number <= 29 and not 69 <= number <= 83:
            extra.append(line)
    try:
        identity, benefit, years = values[1], values[3], values[6]
        if len(identity) != 18 or identity[9] not in "01" or len(years) != 8:
            raise ValueError("Malformed identity/years record")
        kind = BenefitType(int(benefit[0]))
        first, last = int(years[:4]), int(years[4:])
        if 10 in values and 9 not in values:
            raise ValueError("Record 10 requires record 09")
        expected_rows = set(range(22, 22 + (last - first) // 10 + 1))
        if {number for number in values if 22 <= number <= 29} != expected_rows:
            raise ValueError("Earnings rows do not match the declared year span")
        earnings = {}
        for index, start in enumerate(range(first, last + 1, 10)):
            row = values[22 + index]
            count = min(10, last - start + 1)
            if len(row) != count * 11:
                raise ValueError("Earnings row has the wrong fixed width")
            for offset in range(count):
                earnings[start + offset] = money(row[offset * 11:(offset + 1) * 11].strip())
        periods = []
        for number in (9, 10):
            if number not in values:
                continue
            row = values[number]
            if len(row) not in (20, 46):
                raise ValueError("Expected twenty- or forty-six-column disability record")
            periods.append(DisabilityPeriod(_parse_date(row[:8]), Month.parse(row[8:14]), Month.parse(row[14:20]), Month.parse(row[20:26]) if len(row) == 46 else None, money(row[26:36].strip()) if len(row) == 46 else Decimal(0), money(row[36:46].strip()) if len(row) == 46 else Decimal(0)))
        family = []
        for number in range(69, 84):
            if number not in values:
                continue
            if number != 69 + len(family):
                raise ValueError("Family records must be consecutive from 69")
            row = values[number]
            if len(row) != (24 if row.startswith("W") else 16):
                raise ValueError("Family record has the wrong fixed width")
            family.append(FamilyMember(row[:2], _parse_date(row[2:10]), Month.parse(row[10:16]), _parse_date(row[16:24]) if row.startswith("W") else None))
        return Case(identity[:9], _parse_date(identity[10:]), "female" if identity[9] == "1" else "male", kind, None if kind == BenefitType.SURVIVOR else Month.parse(benefit[1:7]), earnings, Month.parse(values[4]) if 4 in values else None, _parse_date(values[2]) if 2 in values else None, tuple(periods), tuple(family), values.get(16, ""), tuple(extra))
    except (KeyError, IndexError) as error:
        raise ValueError(f"Missing or incomplete required record: {error}") from error


def dumps_many(cases: Iterable[Case]) -> str:
    return "".join(dumps(case) for case in cases)


def loads_many(text: str) -> list[Case]:
    groups: list[list[str]] = []
    for line in text.splitlines():
        if line.startswith("01"):
            groups.append([])
        if not groups:
            raise ValueError("Expected initial record 01")
        groups[-1].append(line)
    return [loads("\n".join(group) + "\n") for group in groups]


def to_dict(case: Case) -> dict:
    return {
        "ssn": case.ssn, "birth_date": case.birth_date.isoformat(), "sex": case.sex,
        "benefit_type": case.benefit_type.name.lower(), "entitlement": case.entitlement.iso() if case.entitlement else None,
        "earnings": {str(year): str(amount) for year, amount in case.earnings.items()},
        "benefit_date": case.benefit_date.iso() if case.benefit_date else None,
        "death_date": case.death_date.isoformat() if case.death_date else None,
        "disability": [{"onset": p.onset.isoformat(), "entitlement": p.entitlement.iso(), "waiting": p.waiting.iso(), "cessation": p.cessation.iso() if p.cessation else None, "cessation_pia": str(p.cessation_pia), "cessation_mfb": str(p.cessation_mfb)} for p in case.disability],
        "family": [{"bic": m.bic, "birth_date": m.birth_date.isoformat(), "entitlement": m.entitlement.iso(), "onset": m.onset.isoformat() if m.onset else None} for m in case.family],
        "name": case.name, "extra_records": list(case.extra_records),
    }


def from_dict(value: dict) -> Case:
    return Case(
        value["ssn"], date.fromisoformat(value["birth_date"]), value["sex"], BenefitType[value["benefit_type"].upper()],
        Month.from_iso(value["entitlement"]) if value.get("entitlement") else None,
        {int(year): money(amount) for year, amount in value["earnings"].items()},
        Month.from_iso(value["benefit_date"]) if value.get("benefit_date") else None,
        date.fromisoformat(value["death_date"]) if value.get("death_date") else None,
        tuple(DisabilityPeriod(date.fromisoformat(p["onset"]), Month.from_iso(p["entitlement"]), Month.from_iso(p["waiting"]), Month.from_iso(p["cessation"]) if p.get("cessation") else None, money(p.get("cessation_pia", 0)), money(p.get("cessation_mfb", 0))) for p in value.get("disability", [])),
        tuple(FamilyMember(m["bic"], date.fromisoformat(m["birth_date"]), Month.from_iso(m["entitlement"]), date.fromisoformat(m["onset"]) if m.get("onset") else None) for m in value.get("family", [])),
        value.get("name", ""), tuple(value.get("extra_records", [])),
    )


_OUTPUT_HEAD = re.compile(r"^(\d{3}-\d{2}-\d{4}) (\d{2}/\d{2}/\d{4})")
_PRIMARY_TAIL = re.compile(r"^\s*(\d+) and\s*(\d+) months?\s+(.) ([TF])$")
_FAMILY_TAIL = re.compile(r"^ (.) (.{2}) ([TF])$")


def parse_output(text: str) -> dict:
    """Parse the unmodified non-Statement savecase() output, including messages.

    PIA/MFB/full/rounded amounts have width eight. Fixed-width parsing also
    handles adjacent amounts without whitespace. Granular insured-status
    results are absent from SSA's output and explicitly remain None.
    """
    benefits, messages = [], []
    for line in text.splitlines():
        head = _OUTPUT_HEAD.match(line)
        if not head:
            if line:
                messages.append(line)
            continue
        offset = head.end()
        try:
            pia, mfb, amount = [money(line[offset + n * 8:offset + (n + 1) * 8].strip()) for n in range(3)]
            tail = line[offset + 24:]
            primary = _PRIMARY_TAIL.fullmatch(tail)
            if primary:
                row = {"role": "worker", "bic": "A ", "full_benefit": None, "benefit": str(amount), "age_years": int(primary[1]), "age_months": int(primary[2]), "method": primary[3], "insured": primary[4] == "T"}
            else:
                rounded = money(tail[:8].strip())
                family = _FAMILY_TAIL.fullmatch(tail[8:])
                if not family:
                    raise ValueError("Unknown family output tail")
                row = {"role": "family", "bic": family[2], "full_benefit": str(amount), "benefit": str(rounded), "method": family[1], "insured": family[3] == "T"}
            row.update({"ssn": head[1].replace("-", ""), "birth_date": _parse_date(head[2].replace("/", "")).isoformat(), "primary_insurance_amount": str(pia), "maximum_family_benefit": str(mfb)})
            benefits.append(row)
        except Exception as error:
            raise ValueError(f"Could not parse calculator row {line!r}: {error}") from error
    amounts = {(row["primary_insurance_amount"], row["maximum_family_benefit"]) for row in benefits}
    if len(amounts) > 1:
        # A combined file can contain several workers; use the row values then.
        pia, mfb = None, None
    elif amounts:
        pia, mfb = next(iter(amounts))
    else:
        pia, mfb = None, None
    insurance = {row["insured"] for row in benefits}
    return {"primary_insurance_amount": pia, "maximum_family_benefit": mfb, "benefits": benefits,
            "insured_status": {"combined": next(iter(insurance)) if len(insurance) == 1 else None,
                               "fully": None, "currently": None, "disability": None}, "messages": messages}


def generate_cases(count: int, seed: int = 0) -> Iterable[Case]:
    """Seeded, structurally valid families cycling retirement/disability/survivor.

    Years end by 2024 to avoid forecast assumptions. Earnings begin no earlier
    than 1978 so pre-1978 summary-quarter inputs are unnecessary. This generator
    samples ordinary positive covered earnings, not every statutory edge case.
    """
    if count < 0:
        raise ValueError("Count cannot be negative")
    rng = random.Random(seed)
    for index in range(count):
        kind = (BenefitType.RETIREMENT, BenefitType.DISABILITY, BenefitType.SURVIVOR)[index % 3]
        sex = rng.choice(("male", "female"))
        month, day = rng.randint(1, 12), rng.randint(2, 28)
        family: list[FamilyMember] = []
        disability: tuple[DisabilityPeriod, ...] = ()
        death = None
        if kind == BenefitType.RETIREMENT:
            birth_year = rng.randint(1950, 1954)
            # Begin after the 62nd birthday month; avoid a nominal age-62 year
            # paired with an earlier month that is actually age 61.
            age_months = rng.randint(62 * 12 + 1, min(70 * 12, (2024 - birth_year) * 12 + 12 - month))
            entitlement = Month(birth_year, month).add(age_months)
            benefit = None
            last_year = entitlement.year - 1
            if rng.random() < 0.5:
                family.append(FamilyMember("B ", date(birth_year - rng.randint(0, 3), month, day), entitlement))
        elif kind == BenefitType.DISABILITY:
            birth_year = rng.randint(1955, 1980)
            onset = date(rng.randint(max(2000, birth_year + 30), min(2023, birth_year + 60)), month, day)
            waiting = Month(onset.year, onset.month).add(1)
            entitlement = waiting.add(5)
            benefit = None
            last_year = onset.year - 1
            disability = (DisabilityPeriod(onset, entitlement, waiting),)
            if rng.random() < 0.6:
                family.append(FamilyMember("C1", date(entitlement.year - rng.randint(1, 16), month, day), entitlement))
        else:
            birth_year = rng.randint(1955, 1980)
            death = date(rng.randint(max(2000, birth_year + 30), min(2023, birth_year + 65)), month, day)
            entitlement = None
            benefit = Month(death.year, death.month).add(1)
            last_year = death.year - 1
            for child_index in range(rng.randint(1, 3)):
                family.append(FamilyMember(f"C{child_index + 1}", date(death.year - rng.randint(1, 15), month, day), benefit))
            if rng.random() < 0.5:
                family.append(FamilyMember("E ", date(birth_year + rng.randint(-3, 3), month, day), benefit))
        first_year = max(1978, birth_year + 22)
        earnings = {year: Decimal(rng.randint(500000, 11000000)) / 100 for year in range(first_year, last_year + 1)}
        yield Case(f"{index + 1:09d}", date(birth_year, month, day), sex, kind, entitlement, earnings,
                   benefit, death, disability, tuple(family), f"Generated {kind.name.lower()} {index + 1}")
