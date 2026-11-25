import hashlib
import json
import shutil
import subprocess

import pytest

from infinity_army_acquisition.history_git import recover


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()


def write(repo, name, value):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def commit(repo, name):
    git(repo, "add", "-A")
    git(repo, "commit", "-m", name)
    return git(repo, "rev-parse", "HEAD")


def faction(version):
    return json.dumps({"version": version, "units": [{"factions": [998, 999]}]}).encode()


def metadata(*ids):
    return json.dumps({"factions": [{"id": i, "slug": "backup", "name": "Backup"} for i in ids]}).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.mark.skipif(shutil.which("git") is None, reason="Git is required for local recovery")
def test_recover_bare_history_deleted_blobs_context_and_order(tmp_path):
    repo = tmp_path / "source"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "config", "core.autocrlf", "false")
    path1 = "n5/backup/7.26329.478.json"
    path2 = "n5/backup/7.26329.479.json"
    raw1, raw2 = faction("7.26329.478"), faction("7.26329.479")
    write(repo, "n5/army.json", metadata(998))
    write(repo, path1, raw1)
    first = commit(repo, "first observation")
    write(repo, "n5/army.json", metadata(998, 999))
    write(repo, path2, raw2)
    write(repo, "n5/backup-998/7.26329.479.json", raw2)
    second = commit(repo, "second observation")
    (repo / path1).unlink()
    tip = commit(repo, "remove old path")
    mirror = tmp_path / "bare.git"
    subprocess.run(["git", "clone", "--mirror", str(repo), str(mirror)], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    chronology = tmp_path / "chronology.json"
    rows = [{"member": "root/" + p, "sha256": digest(raw), "edition": "n5",
             "factionId": None, "identityStatus": "ambiguous-folder-and-membership",
             "issues": []} for p, raw in ((path1, raw1), (path2, raw2))]
    chronology.write_text(json.dumps({
        "format": "InfinityDB historical Army chronology", "formatVersion": 1,
        "documents": rows,
        "sequences": [{"edition": "n5", "factionId": 998, "observations": [{
            "encodedRevisionDate": "2026-11-25", "sameDayOrder": "unknown",
            "contents": [{"sha256": row["sha256"], "members": [row["member"]]} for row in rows],
        }]}],
    }), encoding="utf-8")
    report = recover(mirror, "refs/heads/main", chronology)
    assert report == recover(mirror, tip, chronology) | {"source": report["source"]}
    assert report["source"]["tipCommit"] == tip
    assert report["summary"]["commitsScanned"] == 3
    assert report["summary"]["metadataDocuments"] == 2
    assert report["summary"]["factionDocuments"] == 3
    assert report["summary"]["historicalFactionPathsAbsentAtTip"] == 1
    assert report["summary"]["zipFactionDocumentsMatched"] == 2
    assert report["summary"]["previouslyUnresolvedWithCandidate"] == 2
    candidates = report["comparison"]["documents"]
    assert candidates[0]["firstObservation"]["commit"] == first
    assert candidates[0]["proposedFactionId"] == 998
    assert candidates[1]["firstObservation"]["commit"] == second
    assert candidates[1]["status"] == "historical-byte-alias-candidate"
    assert candidates[1]["proposedFactionId"] == 998
    group = report["comparison"]["sameDayGroups"][0]
    assert group["backupObservationOrder"] == "distinct-first-parent-commits"
    assert group["upstreamPublicationOrder"] == "unknown"
    assert report["commits"][-1]["removedPaths"] == [path1]
    assert git(mirror, "rev-parse", "--is-bare-repository") == "true"
    assert git(mirror, "rev-parse", "HEAD") == tip
