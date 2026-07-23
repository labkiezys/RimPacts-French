#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the RimPacts French release archive.")
    parser.add_argument("--version", required=True)
    return parser.parse_args()


def manifest() -> list[Path]:
    files = [ROOT / "About" / "About.xml", ROOT / "About" / "Preview.png"]
    files.extend(sorted((ROOT / "Languages" / "French").rglob("*.xml")))
    return files


def validate(files: list[Path]) -> None:
    if len(files) != 19:
        raise ValueError(f"Expected 19 files, found {len(files)}")
    for path in files:
        if path.is_symlink() or not path.is_file() or ROOT not in path.resolve().parents:
            raise ValueError(f"Unsafe package path: {path}")
        if path.suffix == ".xml":
            ET.parse(path)
    about = ET.parse(ROOT / "About" / "About.xml").getroot()
    if about.findtext("packageId") != "kiezys.rimpacts.fr":
        raise ValueError("Unexpected packageId")
    if about.findtext("./modDependencies/li/packageId") != "wowgag.RimPacts":
        raise ValueError("Unexpected RimPacts dependency")


def build(version: str) -> Path:
    if not VERSION_RE.fullmatch(version):
        raise ValueError(f"Invalid version: {version}")
    files = manifest()
    validate(files)
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    destination = dist / f"RimPacts-French-{version}.zip"
    with tempfile.NamedTemporaryFile(dir=dist, suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for source in files:
                member = Path("RimPacts-French") / source.relative_to(ROOT)
                info = zipfile.ZipInfo(member.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, source.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError("Archive CRC validation failed")
            if len(archive.namelist()) != len(files):
                raise ValueError("Archive manifest mismatch")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


if __name__ == "__main__":
    archive = build(parse_args().version)
    print(archive)
