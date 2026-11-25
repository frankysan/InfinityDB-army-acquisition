"""Recover historical Army observations from local Git objects, without checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from infinity_army_acquisition.history_chronology import folder_candidates
from infinity_army_acquisition.history_inventory import EDITIONS, VERSION, SOURCE, write_inventory
from infinity_army_acquisition.metadata import decode_metadata
from infinity_army_acquisition.source_document import decode_document
from infinity_army_acquisition.source_version import army_source_version_date


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def army_path(path: str) -> tuple[str, str | None, str | None] | None:
    parts = path.split("/")
    if parts[0] not in EDITIONS:
        return None
    if len(parts) == 2 and parts[1] == "army.json":
        return parts[0], None, None
    if len(parts) == 3 and VERSION.fullmatch(parts[2]):
        if parts[1] in ("", ".", "..") or "\\" in path:
            raise ValueError(f"Unsafe Army path: {path}")
        return parts[0], parts[1], parts[2][:-5]
    return None


class Git:
    def __init__(self, repository: Path):
        if not repository.is_dir():
            raise ValueError("Git repository directory does not exist")
        self.command = ["git", "--no-replace-objects", "--no-optional-locks",
                        "-C", str(repository.resolve())]
        self.env = os.environ.copy()
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
            self.env.pop(key, None)
        self.env.update(GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")

    def run(self, *args: str) -> bytes:
        return subprocess.run(
            [*self.command, *args], env=self.env, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout

    def tree(self, commit: str) -> dict[str, str]:
        result = {}
        for entry in self.run("ls-tree", "-r", "-z", "--full-tree", commit, "--", *EDITIONS).split(b"\0"):
            if not entry:
                continue
            header, name = entry.split(b"\t", 1)
            mode, kind, oid = header.decode("ascii").split()
            path = name.decode("utf-8", errors="surrogateescape")
            if army_path(path) is None:
                continue
            if kind != "blob" or mode not in ("100644", "100755"):
                raise ValueError(f"Unexpected Git object mode for {path}")
            result[path] = oid
        return result

    def blobs(self) -> BlobReader:
        return BlobReader(self)


class BlobReader:
    """Use Git's batch protocol to avoid one subprocess per historical blob."""
    def __init__(self, git: Git):
        self.git = git

    def __enter__(self) -> BlobReader:
        self.process = subprocess.Popen(
            [*self.git.command, "cat-file", "--batch"], env=self.git.env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.process.stdin.close()
        if exc_type:
            self.process.terminate()
        self.process.stdout.close()
        code = self.process.wait()
        if code and exc_type is None:
            raise ValueError("Git blob reader failed")

    def read(self, oid: str) -> bytes:
        if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid):
            raise ValueError("Invalid Git blob ID")
        stream = self.process.stdout
        self.process.stdin.write(oid.encode("ascii") + b"\n")
        self.process.stdin.flush()
        header = stream.readline().decode("ascii").split()
        if len(header) != 3 or header[:2] != [oid, "blob"]:
            raise ValueError(f"Missing or invalid Git blob: {oid}")
        size = int(header[2])
        if not 0 <= size <= 32 * 1024 * 1024:
            raise ValueError(f"Unsupported Army blob size: {size}")
        raw = stream.read(size)
        if len(raw) != size or stream.read(1) != b"\n":
            raise ValueError(f"Truncated Git blob: {oid}")
        return raw


def describe_blob(path: str, oid: str, raw: bytes) -> dict:
    edition, folder, revision = army_path(path)
    row = {"path": path, "blob": oid, "edition": edition, "folder": folder,
           "filenameRevision": revision, "sha256": sha256(raw), "sizeBytes": len(raw),
           "issues": []}
    try:
        if folder is None:
            row["kind"] = "metadata"
            row["factions"] = decode_metadata(raw, path)["data"]["factions"]
        else:
            row["kind"] = "faction"
            data = decode_document(raw, path)
            version = data.get("version")
            row["sourceRevision"] = version
            changed_on = army_source_version_date(version)
            row["encodedRevisionDate"] = changed_on.isoformat() if changed_on else None
            if version != revision:
                row["issues"].append("filename-revision-mismatch")
            if not changed_on:
                row["issues"].append("unknown-revision-date")
    except ValueError:
        row["issues"].append("invalid-source-shape")
    return row


def relative_army_path(member: str) -> str:
    if army_path(member):
        return member
    _, separator, tail = member.partition("/")
    if separator and army_path(tail):
        return tail
    raise ValueError(f"Invalid chronology member: {member}")


def compare_chronology(report: dict, prior: dict) -> dict:
    if prior.get("format") != "InfinityDB historical Army chronology" or prior.get("formatVersion") != 1:
        raise ValueError("Expected historical chronology v1")
    by_path_hash = {(d["path"], d["sha256"]): d for d in report["documents"] if d["kind"] == "faction"}
    prior_by_path = {r["member"]: r for r in prior["documents"]}
    by_content = defaultdict(list)
    for doc in by_path_hash.values():
        if not doc["issues"]:
            by_content[(doc["edition"], doc["sha256"])].append(doc)
    comparisons = []
    for row in prior["documents"]:
        doc = by_path_hash.get((relative_army_path(row["member"]), row["sha256"]))
        candidates = set()
        aliases = []
        if doc and not doc["issues"]:
            for alias in by_content[(doc["edition"], doc["sha256"])]:
                ids = alias["firstObservation"]["folderCandidateIds"]
                if len(ids) == 1:
                    candidates.update(ids)
                    aliases.append({"path": alias["path"], "blob": alias["blob"],
                                    "commit": alias["firstObservation"]["commit"], "factionId": ids[0]})
        existing = row["factionId"]
        proposal = None
        if existing is not None and candidates and candidates != {existing}:
            status = "conflicting-historical-candidate"
        elif existing is not None:
            status = "prior-assignment-retained"
        elif len(candidates) == 1 and doc and not row["issues"]:
            proposal = next(iter(candidates))
            status = "historical-folder-candidate" if aliases and any(a["path"] == doc["path"] for a in aliases) else "historical-byte-alias-candidate"
        else:
            status = "unresolved"
        comparisons.append({
            "member": row["member"], "sha256": row["sha256"], "edition": row["edition"],
            "previousFactionId": existing, "previousIdentityStatus": row["identityStatus"],
            "gitMatch": doc is not None, "historicalCandidateIds": sorted(candidates),
            "proposedFactionId": proposal, "status": status, "candidateEvidence": aliases,
            "firstObservation": doc["firstObservation"] if doc else None,
        })

    same_day = []
    for seq in prior["sequences"]:
        for day in seq["observations"]:
            if day["sameDayOrder"] != "unknown":
                continue
            contents = []
            for content in day["contents"]:
                matches = []
                for member in content["members"]:
                    if member not in prior_by_path:
                        raise ValueError("Unknown member in chronology sequence")
                    doc = by_path_hash.get((relative_army_path(member), content["sha256"]))
                    if doc:
                        matches.append(doc["firstObservation"])
                first = min(matches, key=lambda obs: obs["commitIndex"]) if matches else None
                contents.append({"sha256": content["sha256"], "firstObservation": first})
            indices = [c["firstObservation"]["commitIndex"] for c in contents if c["firstObservation"]]
            ordered = len(indices) == len(contents) and len(set(indices)) == len(contents)
            if ordered:
                contents.sort(key=lambda c: c["firstObservation"]["commitIndex"])
            same_day.append({
                "edition": seq["edition"], "factionId": seq["factionId"],
                "encodedRevisionDate": day["encodedRevisionDate"],
                "backupObservationOrder": "distinct-first-parent-commits" if ordered else "unknown",
                "upstreamPublicationOrder": "unknown", "contents": contents,
            })
    return {
        "summary": {
            "zipFactionDocumentsMatched": sum(c["gitMatch"] for c in comparisons),
            "previouslyUnresolvedWithCandidate": sum(c["proposedFactionId"] is not None for c in comparisons),
            "previouslyUnresolvedWithoutCandidate": sum(
                c["previousFactionId"] is None and c["proposedFactionId"] is None for c in comparisons),
            "priorAssignmentsWithConflictingCandidates": sum(
                c["status"] == "conflicting-historical-candidate" for c in comparisons),
            "sameDayGroupsCompared": len(same_day),
            "sameDayGroupsWithDistinctBackupObservations": sum(
                g["backupObservationOrder"] == "distinct-first-parent-commits" for g in same_day),
        },
        "documents": comparisons, "sameDayGroups": same_day,
    }


def recover(repository: Path, ref: str, chronology_path: Path) -> dict:
    git = Git(repository)
    if git.run("rev-parse", "--is-shallow-repository").strip() != b"false":
        raise ValueError("Shallow Git history is not supported")
    if not (ref.startswith("refs/heads/") or re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", ref)):
        raise ValueError("Select a full branch ref or commit ID")
    tip = git.run("rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    raw_log = git.run("log", "--first-parent", "--full-history", "--reverse",
                      "--format=%H%x09%cI", tip, "--", *EDITIONS)
    commits = []
    documents = {}
    cache = {}
    previous_tree = {}
    with git.blobs() as blobs:
        for line in raw_log.decode("ascii").splitlines():
            commit, committed_at = line.split("\t", 1)
            index = len(commits)
            tree = git.tree(commit)
            # Metadata belongs to the tree at observation, not the newest retained copy.
            metadata = {}
            for edition in EDITIONS:
                path = f"{edition}/army.json"
                if path in tree:
                    key = (path, tree[path])
                    if key not in cache:
                        cache[key] = describe_blob(path, tree[path], blobs.read(tree[path]))
                    metadata[edition] = cache[key]
            changes = []
            for path, oid in sorted(tree.items()):
                if previous_tree.get(path) == oid:
                    continue
                key = (path, oid)
                if key not in cache:
                    cache[key] = describe_blob(path, oid, blobs.read(oid))
                row = cache[key]
                context = metadata.get(row["edition"])
                ids = (folder_candidates(row["folder"], context.get("factions", []))
                       if row["folder"] is not None and context and not context["issues"] else set())
                observation = {
                    "commit": commit, "commitIndex": index, "committedAt": committed_at,
                    "metadataBlob": context["blob"] if context else None,
                    "folderCandidateIds": sorted(ids),
                }
                if key not in documents:
                    documents[key] = {**row, "firstObservation": observation, "appearances": []}
                documents[key]["appearances"].append(observation)
                changes.append({"path": path, "blob": oid, "previousBlob": previous_tree.get(path)})
            removed = sorted(set(previous_tree) - set(tree))
            commits.append({"commit": commit, "committedAt": committed_at, "commitIndex": index,
                            "metadataBlobs": {e: m["blob"] for e, m in metadata.items()},
                            "changes": changes, "removedPaths": removed})
            previous_tree = tree
    rows = sorted(documents.values(), key=lambda d: (d["path"], d["blob"]))
    if not any(d["kind"] == "faction" for d in rows):
        raise ValueError("No versioned faction observations recovered")
    prior_raw = chronology_path.read_bytes()
    report = {
        "format": "InfinityDB historical Army Git recovery", "formatVersion": 1,
        "source": {"repository": SOURCE, "selectedRef": ref, "tipCommit": tip,
                   "historyScope": "selected-ref-first-parent-Army-path-history",
                   "coherence": "unverified", "language": "en"},
        "chronologySha256": sha256(prior_raw),
        "summary": {
            "commitsScanned": len(commits), "documents": len(rows),
            "factionDocuments": sum(d["kind"] == "faction" for d in rows),
            "metadataDocuments": sum(d["kind"] == "metadata" for d in rows),
            "metadataByEdition": dict(sorted(Counter(
                d["edition"] for d in rows if d["kind"] == "metadata").items())),
            "documentsWithIssues": sum(bool(d["issues"]) for d in rows),
            "historicalFactionPathsAbsentAtTip": sum(
                d["kind"] == "faction" and d["path"] not in previous_tree for d in rows),
            "historicalFactionPathBlobsNotAtTip": sum(
                d["kind"] == "faction" and previous_tree.get(d["path"]) != d["blob"] for d in rows),
        },
        "commits": commits, "documents": rows,
    }
    comparison = compare_chronology(report, json.loads(prior_raw))
    report["summary"].update(comparison["summary"])
    report["comparison"] = comparison
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--ref", default="refs/heads/main")
    parser.add_argument("--chronology", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.output.resolve().is_relative_to(args.repository.resolve()):
            raise ValueError("Write the report outside the source Git repository")
        report = recover(args.repository, args.ref, args.chronology)
        write_inventory(report, args.output)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report["summary"], indent=2))
    print(f"Git recovery -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
