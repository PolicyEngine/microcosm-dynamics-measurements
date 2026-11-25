"""Build the pinned C++ batch application using Apple clang, with at most 4 jobs."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile
from resource_strings import generate

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "work/build"


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    compiler = os.environ.get("CXX", "/usr/bin/clang++")
    version = subprocess.check_output([compiler, "--version"], text=True)
    print(version, flush=True)
    if "Apple clang" not in version:
        raise SystemExit("This build requires Apple clang")
    src = ROOT / "vendor/oactobjs32"
    port = ROOT / "work/ported/anypia32/FormatString.cpp"
    port.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT / "work") as temporary:
        temporary = Path(temporary)
        original = temporary / "anypia32/FormatString.cpp"
        original.parent.mkdir()
        original.write_text((ROOT / "vendor/anypia32/FormatString.cpp").read_text())
        subprocess.run(["patch", "-p1", "--batch", "--forward", "-i", str(ROOT / "patches/0001-console-resource-strings.patch")], cwd=temporary, check=True)
        data = original.read_bytes()
        if not port.exists() or port.read_bytes() != data:
            port.write_bytes(data)
    generate(ROOT, BUILD / "ResourceStrings.h")
    flags = ["-std=c++14", "-O1", "-g", "-DANYPIAB", "-DONEBIGFILE", "-DDETAILS"]
    flags += ["-I" + str(p) for p in (src / "include", src / "windows", src, ROOT / "vendor/boost_1_81_0", ROOT / "vendor/anypiab", BUILD)]
    sources = [p for d in ("misc", "piadata", "piaout") for p in sorted((src / d).glob("*.cpp"))]
    sources += [src / "windows/BitAnnualBase.cpp", src / "windows/OutFile80.cpp", src / "windows/OutFile132.cpp"]
    sources += sorted((ROOT / "vendor/anypiab").glob("*.cpp"))
    sources.append(port)
    # Invalidate cached objects when compiler flags or any local header changes.
    header_digest = hashlib.sha256()
    header_paths = [p for directory in (src, ROOT / "vendor/anypiab", ROOT / "vendor/boost_1_81_0", BUILD)
                    for p in directory.rglob("*") if p.suffix.lower() in (".h", ".hpp", ".ipp", ".inc")]
    for path in sorted(header_paths):
        header_digest.update(str(path).encode())
        header_digest.update(path.read_bytes())
    signature = json.dumps([version, flags, header_digest.hexdigest()])
    stamp = BUILD / "compile-signature.json"
    compatible_cache = stamp.exists() and stamp.read_text() == signature

    def compile_one(path: Path) -> tuple[Path, int]:
        target = BUILD / (path.parent.name + "_" + path.stem + ".o")
        log = target.with_suffix(".log")
        command = [compiler, *flags, "-c", str(path), "-o", str(target)]
        if compatible_cache and target.exists() and target.stat().st_mtime > path.stat().st_mtime:
            return target, 0
        with log.open("w") as stream:
            stream.write("COMMAND: " + " ".join(command) + "\n")
            stream.flush()
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
            stream.write(f"\nEXIT_CODE={result.returncode}\n")
        if result.returncode:
            print(log.read_text(), flush=True)
        return target, result.returncode

    with ThreadPoolExecutor(max_workers=4) as pool:
        objects = list(pool.map(compile_one, sources))
    failures = sum(code != 0 for _, code in objects)
    print(f"Compiled {len(sources) - failures}/{len(sources)} translation units", flush=True)
    if failures:
        raise SystemExit(1)
    stamp.write_text(signature)
    binary = BUILD / "anypiab"
    subprocess.run([compiler, *(str(path) for path, _ in objects), "-o", str(binary)], check=True)
    print(f"Built {binary}", flush=True)
    # SSA also supplies an embedded source-only sample, selected by this stock
    # main-program macro. Link it against exactly the same calculation objects.
    sample_main = BUILD / "anypiatest_main.o"
    subprocess.run([compiler, *flags, "-UANYPIAB", "-c", str(ROOT / "vendor/anypiab/anypiab.cpp"), "-o", str(sample_main)], check=True)
    sample_objects = [str(path) for path, _ in objects if path.name != "anypiab_anypiab.o"]
    sample_binary = BUILD / "anypiatest"
    subprocess.run([compiler, *sample_objects, str(sample_main), "-o", str(sample_binary)], check=True)
    print(f"Built embedded-source sample {sample_binary}", flush=True)


if __name__ == "__main__":
    main()
