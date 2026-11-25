"""Resolve source faction evidence and group observed historical revisions."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from infinity_army_acquisition.history_inventory import inventory_zip, write_inventory
from infinity_army_acquisition.metadata import decode_metadata
from infinity_army_acquisition.snapshot_provenance import sha256_file, validate_snapshot_manifest
from infinity_army_acquisition.source_document import decode_document
from infinity_army_acquisition.source_version import army_source_version_date


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def folder_candidates(folder: str, factions: list[dict]) -> set[int]:
    return {
        f["id"] for f in factions
        if folder in (f.get("slug"), f"{f.get('slug')}-{f['id']}")
    }


def membership_evidence(data: dict) -> tuple[set[int], int, int]:
    """Unit memberships are evidence, not an explicit response faction ID."""
    sets = []
    for unit in data["units"]:
        values = unit.get("factions") if isinstance(unit, dict) else None
        if isinstance(values, list) and values and all(type(v) is int for v in values):
            sets.append(set(values))
    return set.intersection(*sets) if sets else set(), len(sets), len(data["units"])


def resolve_identity(folder_ids: set[int], common: set[int], usable: int,
                     total: int, exact_ids: set[int], known_ids: set[int]) -> tuple[int | None, str]:
    if len(exact_ids) == 1:
        return next(iter(exact_ids)), "direct-byte-match"
    if exact_ids:
        return None, "ambiguous-direct-match"
    if not usable:
        return None, "metadata-only-candidate" if len(folder_ids) == 1 else "missing-memberships"
    if not common:
        return None, "conflicting-memberships"
    if folder_ids:
        overlap = folder_ids & common
        if len(overlap) == 1:
            status = ("inferred-folder-and-membership" if usable == total
                      else "inferred-folder-and-partial-membership")
            return next(iter(overlap)), status
        return None, "ambiguous-folder-and-membership" if overlap else "folder-membership-conflict"
    if usable == total and len(common) == 1 and common <= known_ids:
        return next(iter(common)), "inferred-membership-only"
    return None, "unresolved-folder"


def direct_snapshot(archive: Path, manifest: Path) -> tuple[dict, list[dict], dict]:
    """Load a verified direct English N5 snapshot as comparison evidence."""
    manifest_raw = manifest.read_bytes()
    provenance = json.loads(manifest_raw)
    validate_snapshot_manifest(provenance, archive=archive)
    snapshot = provenance["snapshot"]
    if (provenance["formatVersion"] != 3 or snapshot["type"] != "army"
            or provenance["source"].get("language") != "en"
            or provenance["source"]["url"].rstrip("/") != "https://api.corvusbelli.com/army"
            or snapshot["archive"]["name"] != archive.name):
        raise ValueError("Expected a matching direct English Army v3 snapshot")
    rows = []
    seen = set()
    with ZipFile(archive) as source:
        metadata = decode_metadata(source.read("metadata.json"), "metadata.json")["data"]
        for member in source.infolist():
            if member.is_dir() or member.filename == "metadata.json":
                continue
            match = re.fullmatch(r"(\d+)-[^/\\]+\.json", member.filename)
            if not match:
                raise ValueError(f"Unexpected direct snapshot member: {member.filename}")
            faction_id = int(match.group(1))
            if faction_id in seen:
                raise ValueError(f"Duplicate direct faction ID: {faction_id}")
            seen.add(faction_id)
            raw = source.read(member)
            version = decode_document(raw, member.filename).get("version")
            changed_on = army_source_version_date(version)
            if changed_on is None:
                raise ValueError("Unknown direct source revision date")
            rows.append({"member": member.filename, "factionId": faction_id,
                         "sha256": digest(raw), "sourceRevision": version,
                         "encodedRevisionDate": changed_on.isoformat()})
    if seen != {f["id"] for f in metadata["factions"]} or len(rows) + 1 != snapshot["documentCount"]:
        raise ValueError("Direct snapshot faction set or document count mismatch")
    if max((row["encodedRevisionDate"] for row in rows), default=None) != provenance["source"]["dataChangedOn"]:
        raise ValueError("Direct snapshot encoded revision date mismatch")
    if sha256_file(archive) != snapshot["archive"]["sha256"]:
        raise ValueError("Direct snapshot changed during comparison")
    identity = {"archiveName": archive.name, "archiveSha256": snapshot["archive"]["sha256"],
                "manifestSha256": digest(manifest_raw), "acquiredAt": snapshot["acquiredAt"],
                "edition": "n5", "language": "en"}
    return identity, sorted(rows, key=lambda r: r["factionId"]), metadata


def chronology(source: Path, inventory: Path, direct: Path, manifest: Path) -> dict:
    inventory_raw = inventory.read_bytes()
    indexed = json.loads(inventory_raw)
    if inventory_zip(source) != indexed:
        raise ValueError("Inventory does not match the supplied source archive")
    direct_identity, direct_rows, direct_metadata = direct_snapshot(direct, manifest)
    direct_by_hash = defaultdict(list)
    for row in direct_rows:
        direct_by_hash[row["sha256"]].append(row)
    metadata = {}
    rows = []
    with ZipFile(source) as archive:
        for row in indexed["documents"]:
            if row["kind"] == "metadata" and not row["issues"]:
                raw = archive.read(row["member"])
                if digest(raw) != row["sha256"]:
                    raise ValueError("Metadata changed since inventory")
                metadata[row["edition"]] = decode_metadata(raw, row["member"])["data"]
        for row in indexed["documents"]:
            if row["kind"] != "faction":
                continue
            factions = metadata.get(row["edition"], {}).get("factions", [])
            folder_ids = folder_candidates(row["factionFolder"], factions)
            raw = archive.read(row["member"])
            if digest(raw) != row["sha256"]:
                raise ValueError("Faction document changed since inventory")
            matches = direct_by_hash[row["sha256"]] if row["edition"] == "n5" else []
            exact_ids = {m["factionId"] for m in matches}
            common, usable, total = set(), 0, 0
            if row["issues"]:
                faction_id, status = None, "invalid-inventory-document"
            else:
                common, usable, total = membership_evidence(decode_document(raw, row["member"]))
                faction_id, status = resolve_identity(folder_ids, common, usable, total,
                                                      exact_ids, {f["id"] for f in factions})
                # CodeOne metadata and unit membership arrays use different ID
                # namespaces. Corroborate via the same slug in retained N4
                # metadata, without equating the two editions' identities.
                if row["edition"] == "codeone" and faction_id is None and len(folder_ids) == 1:
                    n4_ids = folder_candidates(row["factionFolder"],
                                               metadata.get("n4", {}).get("factions", []))
                    if len(n4_ids) == 1 and n4_ids <= common:
                        faction_id = next(iter(folder_ids))
                        status = "inferred-codeone-via-n4-membership"
            rows.append({**row, "factionId": faction_id, "identityStatus": status,
                         "folderCandidateIds": sorted(folder_ids), "commonMembershipIds": sorted(common),
                         "unitsWithMembershipEvidence": usable, "unitsExamined": total,
                         "codeoneN4FolderCandidateIds": sorted(folder_candidates(
                             row["factionFolder"], metadata.get("n4", {}).get("factions", [])
                         )) if row["edition"] == "codeone" else [],
                         "directMatches": [m["member"] for m in matches]})
    if sha256_file(source) != indexed["source"]["archiveSha256"]:
        raise ValueError("Source ZIP changed during chronology")

    groups = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["factionId"] is not None and row["encodedRevisionDate"]:
            groups[(row["edition"], row["factionId"])][row["encodedRevisionDate"]].append(row)
    sequences = []
    for (edition, faction_id), days in sorted(groups.items()):
        observations = []
        previous = None
        for day, members in sorted(days.items()):
            contents = defaultdict(list)
            for member in members:
                contents[member["sha256"]].append(member["member"])
            observations.append({
                "encodedRevisionDate": day,
                "daysSincePreviousObservation": (
                    (date.fromisoformat(day) - date.fromisoformat(previous)).days if previous else None
                ),
                "sameDayOrder": "unknown" if len(contents) > 1 else "not-applicable",
                "contents": [{"sha256": sha, "members": sorted(paths)}
                             for sha, paths in sorted(contents.items())],
            })
            previous = day
        sequences.append({"edition": edition, "factionId": faction_id,
                          "folders": sorted({r["factionFolder"] for day in days.values() for r in day}),
                          "coverage": "incomplete-or-unknown", "observations": observations})
    matched = {m for row in rows for m in row["directMatches"]}
    return {
        "format": "InfinityDB historical Army chronology",
        "formatVersion": 1,
        "source": indexed["source"],
        "inventorySha256": digest(inventory_raw),
        "directSnapshot": direct_identity,
        "summary": {
            "factionDocuments": len(rows),
            "identityStatuses": dict(sorted(Counter(r["identityStatus"] for r in rows).items())),
            "sequences": len(sequences),
            "unresolvedDocuments": sum(r["factionId"] is None for r in rows),
            "unresolvedFolders": dict(sorted(Counter(
                f"{r['edition']}/{r['factionFolder']}" for r in rows if r["factionId"] is None
            ).items())),
            "sameDayUnorderedGroups": sum(o["sameDayOrder"] == "unknown"
                                         for s in sequences for o in s["observations"]),
            "directFactionDocuments": len(direct_rows),
            "directFactionDocumentsMatched": len(matched),
            "n5MetadataJsonEqual": metadata.get("n5") == direct_metadata,
        },
        "directUnmatched": [r for r in direct_rows if r["member"] not in matched],
        "documents": rows,
        "sequences": sequences,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--direct", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = chronology(args.source, args.inventory, args.direct, args.manifest)
        write_inventory(report, args.output)
    except (ValueError, OSError, BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report["summary"], indent=2))
    print(f"Chronology -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
