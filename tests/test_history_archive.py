import json
import shutil
import subprocess
from datetime import date, datetime, timezone
from zipfile import ZipFile

import pytest

from infinity_army_acquisition.history_archive import build_archive, verify_archive
from infinity_army_acquisition.history_chronology import chronology
from infinity_army_acquisition.history_git import recover
from infinity_army_acquisition.history_inventory import inventory_zip, write_inventory
from infinity_army_acquisition.history_reconcile import reconcile
from infinity_army_acquisition.snapshot_provenance import build_snapshot_manifest


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()


@pytest.fixture
def inputs(tmp_path):
    if shutil.which("git") is None:
        pytest.skip("Git required for local fixture")
    repo = tmp_path / "source"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    for key, value in (("user.name", "Fixture"), ("user.email", "fixture@example.invalid"),
                       ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
        git(repo, "config", key, value)
    metadata_old = json.dumps({"factions": [{"id": 101, "name": "Old", "slug": "pan"}]}).encode()
    metadata_new = json.dumps({"factions": [{"id": 101, "name": "New", "slug": "pan"}]}).encode()
    faction = json.dumps({"version": "7.26329.478", "units": [{"id": 1, "factions": [101]}]}).encode()
    faction_path = "n5/pan/7.26329.478.json"
    for path, raw in (("n5/army.json", metadata_old), (faction_path, faction)):
        dest = repo / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "first")
    (repo / "n5/army.json").write_bytes(metadata_new)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "second")
    mirror = tmp_path / "mirror.git"
    subprocess.run(["git", "clone", "--mirror", str(repo), str(mirror)], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    backup = tmp_path / "backup.zip"
    with ZipFile(backup, "w") as z:
        z.writestr("backup/n5/army.json", metadata_new)
        z.writestr("backup/" + faction_path, faction)
    direct = tmp_path / "direct.zip"
    with ZipFile(direct, "w") as z:
        z.writestr("metadata.json", metadata_new)
        z.writestr("101-pan.json", faction)
    manifest = tmp_path / "direct.json"
    write_inventory(build_snapshot_manifest(
        direct, snapshot_type="army", acquired_at=datetime(2026, 11, 25, tzinfo=timezone.utc),
        source_url="https://api.corvusbelli.com/army", document_count=2,
        project_root=tmp_path, language="en", source_data_changed_on=date(2026, 11, 25),
    ), manifest)
    inventory = tmp_path / "inventory.json"
    write_inventory(inventory_zip(backup), inventory)
    prior = tmp_path / "chronology.json"
    write_inventory(chronology(backup, inventory, direct, manifest), prior)
    recovery = tmp_path / "recovery.json"
    write_inventory(recover(mirror, "refs/heads/main", prior), recovery)
    reconciled = tmp_path / "reconciled.json"
    write_inventory(reconcile(prior, recovery), reconciled)
    return (backup, inventory, prior, recovery, reconciled, [(direct, manifest)]), mirror


def test_partial_complete_and_immutable_archive(tmp_path, inputs):
    args, mirror = inputs
    partial = tmp_path / "partial.zip"
    complete = tmp_path / "complete.zip"
    with pytest.raises(ValueError, match="Git bytes missing"):
        build_archive(*args, partial)
    assert not partial.exists()
    report = build_archive(*args, partial, allow_partial=True)
    assert report["summary"]["uniqueObjects"] == 2
    assert report["summary"]["missingObjects"] == 1
    assert not report["completeForSelectedInputs"]
    with pytest.raises(ValueError, match="partial"):
        verify_archive(partial)
    assert verify_archive(partial, allow_partial=True) == report

    report = build_archive(*args, complete, mirror=mirror)
    assert report == verify_archive(complete)
    assert report["completeForSelectedInputs"]
    assert report["summary"]["uniqueObjects"] == 3
    assert report["summary"]["sourceObservations"] == 7
    assert report["summary"]["uniqueFactionObjects"] == 1
    assert report["summary"]["uniqueMetadataObjects"] == 2
    duplicate = tmp_path / "duplicate.zip"
    build_archive(*args, duplicate, mirror=mirror)
    original = complete.read_bytes()
    assert duplicate.read_bytes() == original
    with pytest.raises(FileExistsError):
        build_archive(*args, complete, mirror=mirror)
    assert complete.read_bytes() == original

    corrupt = tmp_path / "corrupt.zip"
    with ZipFile(complete) as source, ZipFile(corrupt, "w") as target:
        for member in source.namelist():
            raw = source.read(member)
            target.writestr(member, b"changed" if member.startswith("objects/") else raw)
    with pytest.raises(ValueError, match="Invalid archived object"):
        verify_archive(corrupt)


def test_reject_modified_reconciliation(tmp_path, inputs):
    args, mirror = inputs
    reconciled = args[4]
    report = json.loads(reconciled.read_bytes())
    report["documents"][0]["factionId"] = 999
    reconciled.write_text(json.dumps(report), encoding="utf-8")
    output = tmp_path / "archive.zip"
    with pytest.raises(ValueError, match="Reconciled chronology"):
        build_archive(*args, output, mirror=mirror)
    assert not output.exists()
