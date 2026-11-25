"""Extract pinned source archives as data, rejecting traversal and symlinks."""

from pathlib import Path, PurePosixPath
import hashlib
import stat
import zipfile

ROOT = Path(__file__).resolve().parent


def unpack() -> None:
    for name in ("oactobjs32.zip", "source32.zip"):
        archive = ROOT / "downloads" / name
        with zipfile.ZipFile(archive) as source:
            if sum(info.file_size for info in source.infolist()) > 200_000_000:
                raise ValueError(f"Unpacked source exceeds 200 MB: {name}")
            for info in source.infolist():
                path = PurePosixPath(info.filename)
                mode = info.external_attr >> 16
                if path.is_absolute() or ".." in path.parts or "\\" in info.filename:
                    raise ValueError(f"Unsafe archive path: {info.filename}")
                if stat.S_ISLNK(mode):
                    raise ValueError(f"Archive symlink: {info.filename}")
                target = ROOT / "vendor" / path
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    data = source.read(info)
                    if target.exists() and target.read_bytes() != data:
                        raise ValueError(f"Preserving changed vendor file: {target}")
                    if not target.exists():
                        target.write_bytes(data)
        print(f"Extracted {name}: sha256={hashlib.sha256(archive.read_bytes()).hexdigest()}")
    # The official sample bundle also contains an executable. Extract only the
    # explicitly named case data; the binary remains inert inside the ZIP.
    sample_archive = ROOT / "downloads/anypiabz.zip"
    with zipfile.ZipFile(sample_archive) as source:
        data = source.read("anypiab.pia")
        target = ROOT / "vendor/samples/anypiab.pia"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != data:
            raise ValueError(f"Preserving changed vendor file: {target}")
        if not target.exists():
            target.write_bytes(data)
    print("Extracted sample data only; no supplied executable extracted")


if __name__ == "__main__":
    unpack()
