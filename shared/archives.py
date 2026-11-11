"""Unpack the PDF members of downloaded (untrusted) zip/RAR archives – shared by all countries.

Names are flattened, members are size-capped, RAR goes through bsdtar (official Ubuntu libarchive-tools package,
unpacked without root into .tools/bsdtar at the repo root), which refuses absolute paths and "..".
"""
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

from common import TOOLS

MAX_MEMBER_BYTES = 400 * 1024 * 1024
BSDTAR = TOOLS / "bsdtar" / "usr" / "bin" / "bsdtar"


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s).strip("_")[:150] or "file"


def member_display_name(info: zipfile.ZipInfo) -> str:
    if info.flag_bits & 0x800:  # UTF-8 flag set
        return info.filename
    try:
        return info.filename.encode("cp437").decode("utf-8")
    except UnicodeError:
        return info.filename


def extract_pdfs(zip_path: Path) -> list[tuple[str, Path]]:
    """Unpack PDF members of an (untrusted) zip into <zip stem>__zip/; returns (member name, path)."""
    out_dir = zip_path.with_name(zip_path.stem + "__zip")
    out = []
    with zipfile.ZipFile(zip_path) as z:
        for i, info in enumerate(z.infolist(), 1):
            name = member_display_name(info)
            if info.is_dir() or not name.lower().endswith(".pdf") or info.file_size > MAX_MEMBER_BYTES:
                continue
            dest = out_dir / f"{i:02d}_{safe_name(Path(name.replace(chr(92), '/')).name)}"
            if not dest.exists():
                out_dir.mkdir(parents=True, exist_ok=True)
                written = 0
                with z.open(info) as src, dest.with_suffix(".part").open("wb") as f:
                    while chunk := src.read(1 << 20):
                        written += len(chunk)
                        if written > MAX_MEMBER_BYTES:
                            raise ValueError(f"zip member larger than declared: {name}")
                        f.write(chunk)
                dest.with_suffix(".part").replace(dest)
            out.append((name, dest))
    return out


def extract_pdfs_rar(rar_path: Path) -> list[tuple[str, Path]]:
    """Unpack PDF members of an (untrusted) RAR into <rar stem>__rar/ with bsdtar (which refuses absolute paths and
    "..") via a scratch folder; returns (member name, path) like extract_pdfs."""
    out_dir = rar_path.with_name(rar_path.stem + "__rar")
    listing = subprocess.run([str(BSDTAR), "-tvf", str(rar_path)], capture_output=True, text=True, check=True).stdout
    members = [line.split(None, 8) for line in listing.splitlines() if line.strip()]
    if any(int(m[4]) > MAX_MEMBER_BYTES for m in members if len(m) == 9):
        raise ValueError("rar member over the size cap")
    out = []
    scratch = out_dir / "_x"
    pdfs = [m[8] for m in members if len(m) == 9 and m[0].startswith("-") and m[8].lower().endswith(".pdf")]
    for i, name in enumerate(pdfs, 1):
        dest = out_dir / f"{i:02d}_{safe_name(Path(name.replace(chr(92), '/')).name)}"
        if not dest.exists():
            if not scratch.exists():
                scratch.mkdir(parents=True)
                subprocess.run([str(BSDTAR), "-xf", str(rar_path), "-C", str(scratch), "--no-same-owner",
                                "--no-same-permissions"], capture_output=True, check=True)
            src = scratch / name
            if src.is_symlink() or not src.is_file():
                raise ValueError(f"rar member not a regular file: {name}")
            src.replace(dest)
        out.append((name, dest))
    if scratch.exists():
        shutil.rmtree(scratch)  # leftovers are non-PDF members (the archive itself is kept)
    return out
