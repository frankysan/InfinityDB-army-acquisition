"""Build and verify a private, content-addressed historical Army archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from contextlib import nullcontext
from pathlib import Path
from zipfile import BadZipFile, ZipFile, ZIP_DEFLATED

from infinity_army_acquisition.history_chronology import chronology, direct_snapshot
from infinity_army_acquisition.history_git import Git, describe_blob, recover, relative_army_path, sha256
from infinity_army_acquisition.history_reconcile import reconcile
from infinity_army_acquisition.snapshot_archive import _archive_info
from infinity_army_acquisition.snapshot_provenance import sha256_file

FORMAT = "InfinityDB historical Army source archive"
HEX = re.compile(r"[0-9a-f]{64}")


def object_member(digest: str) -> str:
    if not isinstance(digest, str) or not HEX.fullmatch(digest):
        raise ValueError("Invalid SHA-256 object identity")
    return f"objects/sha256/{digest}.json"


def git_blob_id(raw: bytes, oid: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid):
        raise ValueError("Invalid Git object ID")
    algorithm = "sha1" if len(oid) == 40 else "sha256"
    return hashlib.new(algorithm, f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


class ArchiveWriter:
    def __init__(self, archive: ZipFile):
        self.archive = archive
        self.objects = {}
        self.evidence = {}

    def write(self, name: str, raw: bytes) -> None:
        self.archive.writestr(_archive_info(name), raw, compress_type=ZIP_DEFLATED, compresslevel=6)

    def put(self, raw: bytes, digest: str, size: int) -> None:
        name = object_member(digest)
        if len(raw) != size or sha256(raw) != digest:
            raise ValueError(f"Source object mismatch: {digest}")
        if digest not in self.objects:
            self.write(name, raw)
            self.objects[digest] = size
        elif self.objects[digest] != size or self.archive.read(name) != raw:
            raise ValueError(f"Conflicting bytes for object: {digest}")

    def add_evidence(self, name: str, raw: bytes) -> None:
        path = f"evidence/{name}.json"
        if path in self.evidence:
            raise ValueError(f"Duplicate evidence path: {path}")
        self.write(path, raw)
        self.evidence[path] = sha256(raw)


def summarize(observations: list[dict], objects: dict, missing: dict) -> dict:
    return {
        "sourceObservations": len(observations),
        "observationsBySource": dict(sorted(Counter(r["sourceType"] for r in observations).items())),
        "uniqueObjects": len(objects),
        "missingObjects": len(missing),
        "uniqueObjectBytes": sum(objects.values()),
        "referencedObjectBytes": sum(r["sizeBytes"] for r in observations),
        "unresolvedFactionObservations": sum(
            r["kind"] == "faction" and r["factionId"] is None for r in observations),
        "uniqueFactionObjects": len({r["sha256"] for r in observations
                                    if r["kind"] == "faction" and r["sha256"] in objects}),
        "uniqueMetadataObjects": len({r["sha256"] for r in observations
                                      if r["kind"] == "metadata" and r["sha256"] in objects}),
    }


def verify_archive(path: Path, *, allow_partial: bool = False) -> dict:
    """Verify exact member set, object bytes, evidence hashes and index references."""
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(n.casefold() for n in names)):
            raise ValueError("Duplicate or case-colliding archive members")
        index = json.loads(archive.read("index.json"))
        if index.get("format") != FORMAT or index.get("formatVersion") != 1:
            raise ValueError("Unsupported historical source archive")
        objects, missing = index["objects"], index["missingObjects"]
        if set(objects) & set(missing):
            raise ValueError("Object cannot be both present and missing")
        if index["completeForSelectedInputs"] != (not missing):
            raise ValueError("Inconsistent completeness status")
        if missing and not allow_partial:
            raise ValueError("Historical archive is partial")
        expected = {"index.json"}
        for digest, size in objects.items():
            member = object_member(digest)
            expected.add(member)
            raw = archive.read(member)
            if type(size) is not int or size != len(raw) or sha256(raw) != digest:
                raise ValueError(f"Invalid archived object: {digest}")
        required_evidence = {
            f"evidence/{name}.json" for name in ("inventory", "chronology", "git-recovery", "reconciled")
        } | {f"evidence/direct-{s['archiveSha256']}.json" for s in index["sourceScope"]["directSnapshots"]}
        if set(index["evidence"]) != required_evidence:
            raise ValueError("Missing or unexpected source evidence")
        for member, digest in index["evidence"].items():
            if not re.fullmatch(r"evidence/[a-z0-9-]+\.json", member) or not HEX.fullmatch(digest):
                raise ValueError("Invalid evidence member")
            expected.add(member)
            if sha256(archive.read(member)) != digest:
                raise ValueError(f"Evidence hash mismatch: {member}")
        if set(names) != expected:
            raise ValueError("Unexpected archive member set")
        referenced = set()
        for row in index["observations"]:
            digest = row["sha256"]
            object_member(digest)
            referenced.add(digest)
            if row["sourceType"] not in ("backup-zip", "backup-git", "direct-api"):
                raise ValueError("Unknown source type")
            size = objects.get(digest, missing.get(digest))
            if size is None or row["sizeBytes"] != size:
                raise ValueError("Unresolved object reference or size mismatch")
        if referenced != set(objects) | set(missing):
            raise ValueError("Unreferenced object or missing-object record")
        if summarize(index["observations"], objects, missing) != index["summary"]:
            raise ValueError("Archive summary mismatch")
    return index


def build_archive(backup: Path, inventory: Path, chronology_path: Path, recovery_path: Path,
                  reconciled_path: Path, direct_pairs: list[tuple[Path, Path]], output: Path,
                  *, mirror: Path | None = None, allow_partial: bool = False) -> dict:
    if not direct_pairs:
        raise ValueError("Select at least the direct snapshot used for chronology")
    inputs = {
        "inventory": inventory.read_bytes(), "chronology": chronology_path.read_bytes(),
        "git-recovery": recovery_path.read_bytes(), "reconciled": reconciled_path.read_bytes(),
    }
    indexed, prior, recovery, reconciled = (
        json.loads(inputs[name]) for name in ("inventory", "chronology", "git-recovery", "reconciled")
    )
    if sha256(inputs["inventory"]) != prior["inventorySha256"]:
        raise ValueError("Chronology inventory identity mismatch")
    pairs = sorted(direct_pairs, key=lambda p: (p[0].name, sha256_file(p[0])))
    snapshots = [(archive, manifest, *direct_snapshot(archive, manifest))
                 for archive, manifest in pairs]
    if len({identity["archiveSha256"] for _, _, identity, _, _ in snapshots}) != len(snapshots):
        raise ValueError("Duplicate direct snapshot")
    original = [s for s in snapshots if s[2] == prior["directSnapshot"]]
    if len(original) != 1:
        raise ValueError("Select the original chronology direct snapshot")
    if chronology(backup, inventory, original[0][0], original[0][1]) != prior:
        raise ValueError("Chronology is inconsistent with original source inputs")
    if reconcile(chronology_path, recovery_path) != reconciled:
        raise ValueError("Reconciled chronology is inconsistent with input reports")
    if mirror is not None:
        if output.resolve().is_relative_to(mirror.resolve()):
            raise ValueError("Write output outside the source mirror")
        git = Git(mirror)
        # Recompute the pinned history, not a moving branch. Keep the original
        # requested ref label when comparing the otherwise identical receipt.
        fresh = recover(mirror, recovery["source"]["tipCommit"], chronology_path)
        fresh["source"]["selectedRef"] = recovery["source"]["selectedRef"]
        if fresh != recovery:
            raise ValueError("Git recovery is inconsistent with the selected mirror")
    else:
        git = None
    assignments = {r["member"]: r for r in reconciled["documents"]}
    # Git identity is path-scoped: do not promote an ambiguous path through a
    # content match alone. The reconciled ZIP observations already carry policy.
    by_git_path = {(relative_army_path(r["member"]), r["sha256"]): r
                   for r in reconciled["documents"]}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, prefix=".army-history-", delete=False) as handle:
        staged = Path(handle.name)
    try:
        observations = []
        missing = {}
        with ZipFile(staged, "w") as target:
            writer = ArchiveWriter(target)
            for name, raw in inputs.items():
                writer.add_evidence(name, raw)
            with ZipFile(backup) as source:
                for row in indexed["documents"]:
                    raw = source.read(row["member"])
                    writer.put(raw, row["sha256"], row["sizeBytes"])
                    assignment = assignments.get(row["member"], {})
                    observations.append({
                        **row, "sourceType": "backup-zip",
                        "sourceArchiveSha256": indexed["source"]["archiveSha256"],
                        "factionId": assignment.get("factionId"),
                        "identityStatus": assignment.get("identityStatus"),
                    })
            if sha256_file(backup) != indexed["source"]["archiveSha256"]:
                raise ValueError("Backup archive changed during consolidation")
            with (git.blobs() if git is not None else nullcontext(None)) as blobs:
                for row in recovery["documents"]:
                    digest = row["sha256"]
                    if digest in writer.objects:
                        raw = target.read(object_member(digest))
                    elif blobs is not None:
                        raw = blobs.read(row["blob"])
                    else:
                        raw = None
                    if raw is None:
                        if digest in missing and missing[digest] != row["sizeBytes"]:
                            raise ValueError("Inconsistent missing object size")
                        missing[digest] = row["sizeBytes"]
                    else:
                        if git_blob_id(raw, row["blob"]) != row["blob"]:
                            raise ValueError("Git blob identity mismatch")
                        actual = describe_blob(row["path"], row["blob"], raw)
                        if actual != {k: v for k, v in row.items() if k not in ("firstObservation", "appearances")}:
                            raise ValueError("Git blob description mismatch")
                        writer.put(raw, digest, row["sizeBytes"])
                    assignment = by_git_path.get((row["path"], digest), {})
                    observations.append({
                        **{k: v for k, v in row.items() if k != "factions"},
                        "sourceType": "backup-git", "sourceTipCommit": recovery["source"]["tipCommit"],
                        "factionId": assignment.get("factionId"),
                        "identityStatus": assignment.get("identityStatus", "unresolved" if row["kind"] == "faction" else None),
                    })
            direct_sources = []
            for archive, manifest, identity, rows, _ in snapshots:
                manifest_raw = manifest.read_bytes()
                if sha256(manifest_raw) != identity["manifestSha256"]:
                    raise ValueError("Direct manifest changed during consolidation")
                writer.add_evidence(f"direct-{identity['archiveSha256']}", manifest_raw)
                direct_sources.append(identity)
                with ZipFile(archive) as source:
                    metadata_raw = source.read("metadata.json")
                    metadata_hash = sha256(metadata_raw)
                    writer.put(metadata_raw, metadata_hash, len(metadata_raw))
                    observations.append({
                        "sourceType": "direct-api", "sourceArchiveSha256": identity["archiveSha256"],
                        "member": "metadata.json", "kind": "metadata", "edition": "n5",
                        "sha256": metadata_hash, "sizeBytes": len(metadata_raw), "factionId": None,
                        "acquiredAt": identity["acquiredAt"],
                    })
                    for row in rows:
                        raw = source.read(row["member"])
                        writer.put(raw, row["sha256"], len(raw))
                        observations.append({
                            **row, "sourceType": "direct-api", "kind": "faction", "edition": "n5",
                            "sourceArchiveSha256": identity["archiveSha256"],
                            "sizeBytes": len(raw), "identityStatus": "direct-endpoint",
                            "acquiredAt": identity["acquiredAt"], "metadataSha256": metadata_hash,
                        })
                if sha256_file(archive) != identity["archiveSha256"]:
                    raise ValueError("Direct archive changed during consolidation")
            # A later direct snapshot can supply a previously unavailable Git
            # object. Check that recovered byte identity and description too.
            for row in recovery["documents"]:
                if row["sha256"] in missing and row["sha256"] in writer.objects:
                    raw = target.read(object_member(row["sha256"]))
                    if git_blob_id(raw, row["blob"]) != row["blob"]:
                        raise ValueError("Git blob identity mismatch")
                    if describe_blob(row["path"], row["blob"], raw) != {
                        k: v for k, v in row.items() if k not in ("firstObservation", "appearances")
                    }:
                        raise ValueError("Git blob description mismatch")
                    writer.put(raw, row["sha256"], row["sizeBytes"])
            missing = {k: v for k, v in missing.items() if k not in writer.objects}
            if missing and not allow_partial:
                raise ValueError("Historical Git bytes missing; supply the local mirror")
            for name, path in (("inventory", inventory), ("chronology", chronology_path),
                               ("git-recovery", recovery_path), ("reconciled", reconciled_path)):
                if sha256_file(path) != writer.evidence[f"evidence/{name}.json"]:
                    raise ValueError("Input report changed during consolidation")
            index = {
                "format": FORMAT, "formatVersion": 1,
                "completeForSelectedInputs": not missing,
                "coverage": "incomplete-or-unknown",
                "sourceScope": {"backup": indexed["source"], "git": recovery["source"],
                                "directSnapshots": direct_sources},
                "objects": dict(sorted(writer.objects.items())),
                "missingObjects": dict(sorted(missing.items())),
                "evidence": dict(sorted(writer.evidence.items())),
                "observations": observations,
                "summary": summarize(observations, writer.objects, missing),
            }
            writer.write("index.json", (json.dumps(index, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        verify_archive(staged, allow_partial=allow_partial)
        os.link(staged, output)
    finally:
        staged.unlink(missing_ok=True)
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    for name in ("backup", "inventory", "chronology", "git-recovery", "reconciled", "output"):
        build.add_argument("--" + name, required=True, type=Path)
    build.add_argument("--direct", nargs=2, action="append", required=True, type=Path,
                       metavar=("ZIP", "MANIFEST"))
    build.add_argument("--mirror", type=Path)
    build.add_argument("--allow-partial", action="store_true")
    verify = commands.add_parser("verify")
    verify.add_argument("archive", type=Path)
    verify.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            index = build_archive(args.backup, args.inventory, args.chronology, args.git_recovery,
                                  args.reconciled, args.direct, args.output,
                                  mirror=args.mirror, allow_partial=args.allow_partial)
            output = args.output
        else:
            index = verify_archive(args.archive, allow_partial=args.allow_partial)
            output = args.archive
    except (OSError, ValueError, KeyError, TypeError, BadZipFile, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(index["summary"], indent=2))
    print(f"Complete for selected inputs: {index['completeForSelectedInputs']}")
    print(f"Archive SHA-256: {sha256_file(output)}")
    print(f"Archive -> {output}")
    return 0 if index["completeForSelectedInputs"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
