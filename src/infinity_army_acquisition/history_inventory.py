"""Inventory historical Army source documents without reconstructing snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from infinity_army_acquisition.metadata import decode_metadata
from infinity_army_acquisition.source_document import decode_document
from infinity_army_acquisition.source_version import army_source_version_date

EDITIONS = ("n4", "n5", "codeone")
VERSION = re.compile(r"\d+\.\d+\.\d+\.json")
SOURCE = "https://github.com/massayoshi/infinity-army-backup"


def _candidate(name: str) -> tuple[str, str | None, str | None] | None:
    """Recognize only edition metadata and version-named faction responses."""
    parts = name.split("/")
    if len(parts) >= 2 and parts[0] not in EDITIONS:
        parts = parts[1:]  # GitHub ZIP root directory
    if not parts or parts[0] not in EDITIONS:
        return None
    if len(parts) == 2 and parts[1] == "army.json":
        return parts[0], None, None
    if len(parts) == 3 and VERSION.fullmatch(parts[2]):
        if parts[1] in ("", ".", "..") or "\\" in name:
            raise ValueError(f"Unsafe faction member: {name}")
        return parts[0], parts[1], parts[2][:-5]
    return None


def inventory_zip(source: Path) -> dict:
    """Read the archive without extraction; retain evidence even for invalid rows."""
    rows: list[dict] = []
    seen: set[str] = set()
    roots: set[str] = set()
    with source.open("rb") as stream:
        archive_hash = hashlib.file_digest(stream, "sha256").hexdigest()
        stream.seek(0)
        with ZipFile(stream) as archive:
            for member in sorted(archive.infolist(), key=lambda item: item.filename):
                if member.is_dir():
                    continue
                name = member.filename
                candidate = _candidate(name)
                if candidate is None:
                    continue
                edition, folder, revision = candidate
                parts = name.split("/")
                root = "" if parts[0] in EDITIONS else parts[0]
                if root in (".", "..") or (not root and parts[0] not in EDITIONS):
                    raise ValueError(f"Unsafe archive root: {name}")
                roots.add(root)
                if len(roots) > 1:
                    raise ValueError("Multiple archive roots contain Army documents")
                key = name.casefold()
                if key in seen:
                    raise ValueError(f"Duplicate or case-colliding member: {name}")
                seen.add(key)
                raw = archive.read(member)
                row = {
                    "member": name,
                    "edition": edition,
                    "kind": "metadata" if revision is None else "faction",
                    "factionFolder": folder,
                    "filenameRevision": revision,
                    "sourceRevision": None,
                    "encodedRevisionDate": None,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "sizeBytes": len(raw),
                    "issues": [],
                }
                try:
                    if revision is None:
                        decode_metadata(raw, name)
                    else:
                        data = decode_document(raw, name)
                        version = data.get("version")
                        if isinstance(version, str):
                            row["sourceRevision"] = version
                            changed_on = army_source_version_date(version)
                            if changed_on is not None:
                                row["encodedRevisionDate"] = changed_on.isoformat()
                        if version != revision:
                            row["issues"].append("filename-revision-mismatch")
                        if row["encodedRevisionDate"] is None:
                            row["issues"].append("unknown-revision-date")
                        row["unitCount"] = len(data["units"])
                except ValueError:
                    row["issues"].append("invalid-source-shape")
                rows.append(row)
        stream.seek(0)
        if hashlib.file_digest(stream, "sha256").hexdigest() != archive_hash:
            raise ValueError("Source ZIP changed during inventory")

    if not any(row["kind"] == "faction" for row in rows):
        raise ValueError("No versioned faction documents found")
    counts = Counter(row["sha256"] for row in rows)
    editions = {}
    for edition in EDITIONS:
        faction_rows = [
            row for row in rows if row["edition"] == edition and row["kind"] == "faction"
        ]
        dates = [
            row["encodedRevisionDate"] for row in faction_rows if not row["issues"]
        ]
        editions[edition] = {
            "factionDocuments": len(faction_rows),
            "factionFolders": len({row["factionFolder"] for row in faction_rows}),
            "metadataDocuments": sum(
                row["edition"] == edition and row["kind"] == "metadata" for row in rows
            ),
            "earliestEncodedDate": min(dates, default=None),
            "latestEncodedDate": max(dates, default=None),
        }
    return {
        "format": "InfinityDB historical Army inventory",
        "formatVersion": 1,
        "source": {
            "repository": SOURCE,
            "archiveName": source.name,
            "archiveSha256": archive_hash,
            "language": "en",
            "languageBasis": "archive downloader configuration naming",
            "commit": None,
            "coherence": "unverified",
        },
        "summary": {
            "documents": len(rows),
            "documentsWithIssues": sum(bool(row["issues"]) for row in rows),
            "uniqueByteContents": len(counts),
            "duplicateByteContents": sum(count - 1 for count in counts.values()),
            "editions": editions,
        },
        "documents": rows,
    }


def write_inventory(report: dict, output: Path) -> None:
    """Publish a private report without replacing an existing report or source."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=output.parent, prefix=".history-inventory-", delete=False
    ) as stream:
        staged = Path(stream.name)
        try:
            stream.write((json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        except BaseException:
            stream.close()
            staged.unlink(missing_ok=True)
            raise
    try:
        os.link(staged, output)
    finally:
        staged.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Private GitHub backup ZIP")
    parser.add_argument("--output", required=True, type=Path, help="New inventory JSON")
    args = parser.parse_args(argv)
    try:
        report = inventory_zip(args.source)
        write_inventory(report, args.output)
    except (OSError, ValueError, BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report["summary"], indent=2))
    print(f"Inventory -> {args.output}")
    return 2 if report["summary"]["documentsWithIssues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
