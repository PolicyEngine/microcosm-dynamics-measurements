"""Extract the conservative include closure used by SSA, never Boost tools."""
from pathlib import Path, PurePosixPath
import re
import tarfile

ROOT = Path(__file__).resolve().parent
LIMIT = 200_000_000
REFERENCE = re.compile(rb"boost/[A-Za-z0-9_./-]+\.(?:hpp|h|ipp|inc)")


def extract() -> None:
    # Read header data into memory to follow includes without unpacking the
    # complete archive. No archive member is imported, executed, or evaluated.
    headers: dict[str, bytes] = {}
    with tarfile.open(ROOT / "downloads/boost_1_81_0.tar.bz2", "r|bz2") as archive:
        for member in archive:
            parts = PurePosixPath(member.name).parts
            if len(parts) < 3 or parts[:2] != ("boost_1_81_0", "boost"):
                continue
            if not member.isfile() or ".." in parts:
                continue
            if not member.name.endswith((".hpp", ".h", ".ipp", ".inc")):
                continue
            stream = archive.extractfile(member)
            assert stream is not None
            headers["/".join(parts[1:])] = stream.read()
    seeds = set()
    for path in (ROOT / "vendor").rglob("*"):
        if path.suffix.lower() in (".h", ".cpp", ".c") and "boost_1_81_0" not in path.parts:
            seeds.update(item.decode() for item in REFERENCE.findall(path.read_bytes()))
    # These directories are selected by Boost's macro-generated include names.
    # Include their possible targets conservatively across compiler branches.
    dynamic = ("boost/config/", "boost/preprocessor/", "boost/mpl/aux_/preprocessed/")
    seeds.update(name for name in headers if name.startswith(dynamic))
    selected: set[str] = set()
    pending = list(seeds)
    while pending:
        name = pending.pop()
        if name in selected or name not in headers:
            continue
        selected.add(name)
        pending.extend(item.decode() for item in REFERENCE.findall(headers[name]))
        for relative in re.findall(rb'#\s*include\s*"([^"<>]+)"', headers[name]):
            resolved = str(PurePosixPath(name).parent / relative.decode())
            if resolved in headers:
                pending.append(resolved)
    size = sum(len(headers[name]) for name in selected)
    print(f"Boost header closure: {len(selected)} files, {size} bytes (limit {LIMIT})", flush=True)
    if size > LIMIT:
        raise ValueError("Required Boost headers exceed 200 MB; stopping")
    destination = ROOT / "vendor/boost_1_81_0"
    for name in sorted(selected):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(headers[name])
    (ROOT / "work/boost-headers.txt").write_text("\n".join(sorted(selected)) + "\n")


if __name__ == "__main__":
    extract()
