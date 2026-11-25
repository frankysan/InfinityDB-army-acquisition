"""Reconcile Git-backed historical faction evidence without altering source reports."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from infinity_army_acquisition.history_git import compare_chronology, relative_army_path, sha256
from infinity_army_acquisition.history_inventory import write_inventory


# Reviewed historical downloader versions use metadata IDs to request faction
# data and slugs to store it. Scope the exception to these exact observations:
# CodeOne unit membership arrays are not endpoint identifiers.
CODEONE_REVIEW = {
    "232df7e614304102a49f5e75e31182d668eeb263": "4f973dbb76ce57fb995b4224c5aeee834239d09a",
    "f8962011247fcd88642de4b4b80d6cb635d1bec3": "a844fc9f9f39f266a6e0c9df10c5544902bb2ddd",
}
CODEONE_FOLDERS = {"combined-army": 10601, "nomads": 10501}


def select_identity(row: dict, evidence: dict, prior_alias_ids: set[int]) -> tuple[int | None, str]:
    prior = row["factionId"]
    candidates = set(evidence["historicalCandidateIds"])
    if row["issues"]:
        return None, "invalid-source-document"
    if prior is not None:
        if candidates and candidates != {prior}:
            return None, "conflicting-historical-candidate"
        return prior, row["identityStatus"]
    candidate = evidence["proposedFactionId"]
    if candidate is None or candidates != {candidate} or not evidence["gitMatch"]:
        return None, "unresolved"
    if prior_alias_ids and prior_alias_ids != {candidate}:
        return None, "conflicting-assigned-alias"
    first = evidence["firstObservation"]
    if candidate in row["commonMembershipIds"] and first["folderCandidateIds"] == [candidate]:
        return candidate, "inferred-historical-folder-and-membership"
    if prior_alias_ids == {candidate}:
        return candidate, "inferred-historical-byte-alias"
    if (row["edition"] == "codeone"
            and CODEONE_FOLDERS.get(row["factionFolder"]) == candidate
            and first["commit"] in CODEONE_REVIEW
            and first["folderCandidateIds"] == [candidate]
            and row["identityStatus"] == "conflicting-memberships"):
        return candidate, "inferred-reviewed-codeone-endpoint"
    return None, "candidate-needs-review"


def reconcile(chronology_path: Path, recovery_path: Path) -> dict:
    prior_raw, git_raw = chronology_path.read_bytes(), recovery_path.read_bytes()
    prior, recovery = json.loads(prior_raw), json.loads(git_raw)
    if (recovery.get("format") != "InfinityDB historical Army Git recovery"
            or recovery.get("formatVersion") != 1
            or recovery.get("chronologySha256") != sha256(prior_raw)):
        raise ValueError("Git recovery is not bound to this chronology")
    comparison = compare_chronology(recovery, prior)
    if comparison != recovery["comparison"]:
        raise ValueError("Git comparison is inconsistent with source reports")
    evidence_by_member = {r["member"]: r for r in comparison["documents"]}
    if len(evidence_by_member) != len(prior["documents"]):
        raise ValueError("Duplicate chronology members")
    git_docs = {(r["path"], r["sha256"]): r for r in recovery["documents"]}
    aliases = defaultdict(set)
    for row in prior["documents"]:
        if row["factionId"] is not None and not row["issues"]:
            aliases[(row["edition"], row["sha256"])].add(row["factionId"])
    rows = []
    for row in prior["documents"]:
        evidence = evidence_by_member[row["member"]]
        faction_id, status = select_identity(row, evidence, aliases[(row["edition"], row["sha256"])])
        git_doc = git_docs.get((relative_army_path(row["member"]), row["sha256"]))
        first = evidence["firstObservation"]
        rows.append({
            **row, "priorFactionId": row["factionId"], "priorIdentityStatus": row["identityStatus"],
            "factionId": faction_id, "identityStatus": status,
            "gitBlob": git_doc["blob"] if git_doc else None,
            "firstBackupObservation": first,
            "historicalCandidateIds": evidence["historicalCandidateIds"],
            "candidateEvidence": evidence["candidateEvidence"],
            "reviewedDownloaderBlob": CODEONE_REVIEW[first["commit"]]
                if status == "inferred-reviewed-codeone-endpoint" else None,
        })

    groups = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for row in rows:
        if row["factionId"] is not None and row["encodedRevisionDate"]:
            groups[(row["edition"], row["factionId"])][row["encodedRevisionDate"]][row["sha256"]].append(row)
    sequences = []
    for (edition, faction_id), days in sorted(groups.items()):
        observations = []
        previous = None
        for day, by_hash in sorted(days.items()):
            contents = []
            for digest, members in sorted(by_hash.items()):
                firsts = [r["firstBackupObservation"] for r in members if r["firstBackupObservation"]]
                first = min(firsts, key=lambda f: f["commitIndex"]) if firsts else None
                contents.append({"sha256": digest, "members": sorted(r["member"] for r in members),
                                 "firstBackupObservation": first})
            indices = [c["firstBackupObservation"]["commitIndex"] for c in contents
                       if c["firstBackupObservation"] is not None]
            distinct = len(indices) == len(contents) and len(set(indices)) == len(contents)
            order = ("not-applicable" if len(contents) == 1 else
                     "distinct-first-parent-commits" if distinct else "unknown")
            if distinct:
                contents.sort(key=lambda c: c["firstBackupObservation"]["commitIndex"])
            observations.append({
                "encodedRevisionDate": day,
                "daysSincePreviousObservation": (
                    (date.fromisoformat(day) - date.fromisoformat(previous)).days if previous else None
                ),
                "backupObservationOrder": order,
                "upstreamPublicationOrder": "unknown" if len(contents) > 1 else "not-applicable",
                "contents": contents,
            })
            previous = day
        sequences.append({"edition": edition, "factionId": faction_id,
                          "coverage": "incomplete-or-unknown", "observations": observations})
    remaining = [r for r in rows if r["factionId"] is None]
    metadata = [r for r in recovery["documents"] if r["kind"] == "metadata"]
    return {
        "format": "InfinityDB historical Army reconciled chronology", "formatVersion": 1,
        "source": prior["source"], "directSnapshot": prior["directSnapshot"],
        "gitSource": recovery["source"], "chronologySha256": sha256(prior_raw),
        "gitRecoverySha256": sha256(git_raw),
        "summary": {
            "factionDocuments": len(rows), "assignedDocuments": len(rows) - len(remaining),
            "newAssignments": sum(r["priorFactionId"] is None and r["factionId"] is not None for r in rows),
            "identityStatuses": dict(sorted(Counter(r["identityStatus"] for r in rows).items())),
            "unresolvedDocuments": len(remaining),
            "unresolvedFolders": dict(sorted(Counter(
                f"{r['edition']}/{r['factionFolder']}" for r in remaining).items())),
            "sequences": len(sequences),
            "distinctAssignedFactionContents": sum(len(o["contents"]) for s in sequences for o in s["observations"]),
            "sameDayGroupsOrderedByBackup": sum(o["backupObservationOrder"] == "distinct-first-parent-commits"
                                                for s in sequences for o in s["observations"]),
            "sameDayGroupsUnordered": sum(o["backupObservationOrder"] == "unknown"
                                          for s in sequences for o in s["observations"]),
            "metadataDocuments": len(metadata),
        },
        "documents": rows, "sequences": sequences, "metadataDocuments": metadata,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chronology", required=True, type=Path)
    parser.add_argument("--git-recovery", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        report = reconcile(args.chronology, args.git_recovery)
        write_inventory(report, args.output)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report["summary"], indent=2))
    print(f"Reconciled chronology -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
