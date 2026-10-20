#!/usr/bin/env python3
"""Build a deterministic ZIP containing only the standalone skill directory."""
import hashlib
from pathlib import Path
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "visual-story-production"
VERSION = "0.1.0"


def build(output=None):
    output = Path(output) if output else ROOT / "dist" / f"visual-story-production-v{VERSION}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in SKILL.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    if any(p.is_symlink() for p in files):
        raise ValueError("Refusing to package symlinks")
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for path in files:
            name = "visual-story-production/" + path.relative_to(SKILL).as_posix()
            info = ZipInfo(name, date_time=(2026, 10, 20, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes().replace(b"\r\n", b"\n"))
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(digest + "  " + output.name + "\n", encoding="utf-8")
    return output, digest


def main():
    from check_package import check
    errors = check()
    if errors:
        for error in errors:
            print("ERROR: " + error)
        return 1
    output, digest = build()
    print("Built: " + str(output))
    print("SHA256: " + digest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
