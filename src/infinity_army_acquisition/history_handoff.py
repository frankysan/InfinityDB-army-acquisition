"""Producer-side acceptance of an explicitly pinned historical source archive."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from infinity_army_acquisition.history_archive import HEX, object_member, verify_archive
from infinity_army_acquisition.history_git import relative_army_path
from infinity_army_acquisition.history_inventory import EDITIONS, write_inventory
from infinity_army_acquisition.snapshot_provenance import sha256_file
from infinity_army_acquisition.source_document import decode_document
from infinity_army_acquisition.metadata import decode_metadata
from infinity_army_acquisition.source_version import army_source_version_date


def acceptance(archive_path: Path, expected_sha256: str) -> dict:
    if not HEX.fullmatch(expected_sha256) or sha256_file(archive_path) != expected_sha256:
        raise ValueError("Historical archive SHA-256 mismatch")
    index = verify_archive(archive_path)
    observations = index["observations"]
    groups = defaultdict(set)
    metadata_by_blob = defaultdict(set)
    metadata_by_snapshot = defaultdict(set)
    unresolved = set()
    with ZipFile(archive_path) as archive:
        evidence = {name: json.loads(archive.read(f"evidence/{name}.json"))
                    for name in ("inventory", "chronology", "git-recovery", "reconciled")}
        hashes = index["evidence"]
        inventory, chronology, recovery, reconciled = (
            evidence[name] for name in ("inventory", "chronology", "git-recovery", "reconciled")
        )
        if (chronology["inventorySha256"] != hashes["evidence/inventory.json"]
                or recovery["chronologySha256"] != hashes["evidence/chronology.json"]
                or reconciled["chronologySha256"] != hashes["evidence/chronology.json"]
                or reconciled["gitRecoverySha256"] != hashes["evidence/git-recovery.json"]
                or index["sourceScope"]["backup"] != inventory["source"]
                or index["sourceScope"]["git"] != recovery["source"]):
            raise ValueError("Historical evidence linkage mismatch")
        reconciled_by_member = {r["member"]: r for r in reconciled["documents"]}
        reconciled_by_git = {(relative_army_path(r["member"]), r["sha256"], r["edition"]): r
                             for r in reconciled["documents"] if r["gitBlob"]}
        parsed = {}
        for row in observations:
            edition, kind, digest = row["edition"], row["kind"], row["sha256"]
            if edition not in EDITIONS or kind not in ("faction", "metadata"):
                raise ValueError("Unsupported historical observation kind or edition")
            key = (kind, digest)
            if key not in parsed:
                raw = archive.read(object_member(digest))
                if kind == "metadata":
                    decode_metadata(raw, digest)
                    parsed[key] = None
                else:
                    parsed[key] = decode_document(raw, digest).get("version")
            if kind == "metadata":
                if row["factionId"] is not None:
                    raise ValueError("Metadata has a faction identity")
                if row["sourceType"] == "backup-git":
                    metadata_by_blob[(edition, row["blob"])].add(digest)
                elif row["sourceType"] == "direct-api":
                    metadata_by_snapshot[row["sourceArchiveSha256"]].add(digest)
                continue
            revision = parsed[key]
            day = army_source_version_date(revision)
            if (day is None or row.get("sourceRevision") != revision
                    or row.get("encodedRevisionDate") != day.isoformat() or row.get("issues")):
                raise ValueError("Invalid historical faction revision")
            faction = row["factionId"]
            if faction is not None and type(faction) is not int:
                raise ValueError("Invalid source faction identity")
            if row["sourceType"] == "backup-zip":
                previous = reconciled_by_member.get(row["member"])
                if not previous or (previous["sha256"], previous["factionId"], previous["identityStatus"]) != (
                        digest, faction, row["identityStatus"]):
                    raise ValueError("Historical ZIP identity mismatch")
            elif row["sourceType"] == "backup-git":
                previous = reconciled_by_git.get((row["path"], digest, edition))
                if previous:
                    if (previous["gitBlob"], previous["factionId"], previous["identityStatus"]) != (
                            row["blob"], faction, row["identityStatus"]):
                        raise ValueError("Historical Git identity mismatch")
                elif faction is not None:
                    raise ValueError("Unreviewed Git faction identity")
            elif faction is None or row["identityStatus"] != "direct-endpoint":
                raise ValueError("Invalid direct endpoint identity status")
            if faction is None:
                unresolved.add((edition, digest))
            else:
                groups[(edition, faction, day.isoformat())].add(digest)

        contexts = Counter()
        for row in observations:
            if row["kind"] != "faction":
                continue
            if row["sourceType"] == "backup-git":
                for appearance in row["appearances"]:
                    blob = appearance["metadataBlob"]
                    if blob is None:
                        contexts["gitMissingContext"] += 1
                    elif len(metadata_by_blob[(row["edition"], blob)]) != 1:
                        raise ValueError("Git metadata reference missing or ambiguous")
                    else:
                        contexts["gitObservedContext"] += 1
            elif row["sourceType"] == "direct-api":
                if metadata_by_snapshot[row["sourceArchiveSha256"]] != {row["metadataSha256"]}:
                    raise ValueError("Direct snapshot metadata reference mismatch")
                contexts["directSnapshotContext"] += 1

        # A sequence is evidence for backup ordering, never upstream chronology.
        for sequence in reconciled["sequences"]:
            for observation in sequence["observations"]:
                key = (sequence["edition"], sequence["factionId"], observation["encodedRevisionDate"])
                if not {c["sha256"] for c in observation["contents"]} <= groups[key]:
                    raise ValueError("Reconciled sequence references unknown faction content")
    if sha256_file(archive_path) != expected_sha256:
        raise ValueError("Historical archive changed during acceptance")
    return {
        "format": "InfinityDB historical Army handoff acceptance",
        "formatVersion": 1,
        "archive": {"name": archive_path.name, "sha256": expected_sha256,
                    "sourceFormatVersion": index["formatVersion"]},
        "sourceScope": index["sourceScope"],
        "evidence": index["evidence"],
        "summary": {
            **index["summary"],
            "editionFactionSequences": len({(e, f) for e, f, _ in groups}),
            "assignedFactionDateContents": sum(map(len, groups.values())),
            "assignedSameDayGroups": sum(len(v) > 1 for v in groups.values()),
            "unresolvedEditionContents": len(unresolved),
            "metadataContexts": dict(sorted(contexts.items())),
        },
        "coverage": index["coverage"],
        "consumerAcceptance": "not-tested",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = acceptance(args.archive, args.sha256)
        write_inventory(report, args.output)
    except (OSError, ValueError, KeyError, TypeError, BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report["summary"], indent=2))
    print(f"Handoff acceptance -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
