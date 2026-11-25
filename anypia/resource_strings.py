"""Read SSA's RC string data into a portable lookup; never evaluate source."""
from pathlib import Path
import json
import re


def generate(root: Path, destination: Path) -> None:
    vendor = root / "vendor"
    resource = (vendor / "oactobjs32/include/Resource.h").read_text()
    ids = {name: int(value) for name, value in re.findall(r"^#define\s+(PIA_IDS_\w+)\s+(\d+)", resource, re.M)}
    rc = (vendor / "anypia32/Anypia32.rc").read_text(encoding="cp1252")
    strings: dict[int, str] = {}
    for table in re.findall(r"STRINGTABLE\s+BEGIN(.*?)\bEND\b", rc, re.S):
        for name, literal in re.findall(r'\b(PIA_IDS_\w+)\s+"((?:[^"\\]|\\.|"")*)"', table):
            if name in ids:
                strings[ids[name]] = json.loads('"' + literal.replace('""', '\\"') + '"')
    # Every template referenced by output code must have a real SSA string.
    output_code = "\n".join(p.read_text() for p in (vendor / "oactobjs32/piaout").glob("*.cpp"))
    required = set(re.findall(r"AfxFormatString[12]\([^;]+?(PIA_IDS_\w+)", output_code, re.S))
    missing = {name for name in required if name not in ids or ids[name] not in strings}
    if missing:
        raise ValueError(f"Missing SSA report string resources: {sorted(missing)}")
    lines = ['#pragma once', '#include <stdexcept>', '#include <string>', 'inline std::string ssaResourceString(unsigned int id) {', '  switch (id) {']
    lines += [f'    case {key}: return {json.dumps(value, ensure_ascii=True)};' for key, value in sorted(strings.items())]
    lines += ['    default: throw std::runtime_error("Unknown SSA string resource");', '  }', '}']
    data = "\n".join(lines) + "\n"
    if not destination.exists() or destination.read_text() != data:
        destination.write_text(data)
    print(f"Generated {len(strings)} SSA resource strings for portable report formatting", flush=True)
