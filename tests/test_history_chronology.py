import json
from datetime import date, datetime, timezone
from zipfile import ZipFile

import pytest

from infinity_army_acquisition.history_chronology import (
    chronology, folder_candidates, membership_evidence, resolve_identity,
)
from infinity_army_acquisition.history_inventory import inventory_zip, write_inventory
from infinity_army_acquisition.snapshot_provenance import build_snapshot_manifest


def test_folder_collision_is_not_silently_resolved():
    factions = [{"id": 998, "slug": "backup"}, {"id": 999, "slug": "backup"}]
    assert folder_candidates("backup", factions) == {998, 999}
    assert folder_candidates("backup-998", factions) == {998}
    assert resolve_identity({998, 999}, {998, 999}, 2, 2, set(), {998, 999}) == (
        None, "ambiguous-folder-and-membership"
    )


@pytest.mark.parametrize(("folder", "common", "usable", "total", "exact", "expected"), [
    ({101}, {101, 102}, 3, 3, set(), (101, "inferred-folder-and-membership")),
    (set(), {105}, 2, 2, set(), (105, "inferred-membership-only")),
    ({101}, {105}, 2, 2, set(), (None, "folder-membership-conflict")),
    ({101}, {101}, 1, 2, set(), (101, "inferred-folder-and-partial-membership")),
    ({101}, set(), 0, 2, set(), (None, "metadata-only-candidate")),
    ({101}, {105}, 1, 2, set(), (None, "folder-membership-conflict")),
    ({101}, set(), 2, 2, set(), (None, "conflicting-memberships")),
    ({101}, set(), 0, 0, {105}, (105, "direct-byte-match")),
    ({101}, {101}, 2, 2, {101, 105}, (None, "ambiguous-direct-match")),
])
def test_resolve_identity(folder, common, usable, total, exact, expected):
    assert resolve_identity(folder, common, usable, total, exact, {101, 102, 105}) == expected


def test_memberships_only_use_valid_nonempty_integer_arrays():
    assert membership_evidence({"units": [
        {"factions": [101, 102]}, {"factions": [101, 103]},
        {"factions": []}, {"factions": [True]}, {},
    ]}) == ({101}, 2, 5)


def test_chronology_preserves_dates_duplicate_paths_and_direct_provenance(tmp_path):
    metadata = {"factions": [{"id": 101, "slug": "pan", "name": "Pan"}]}
    raw = json.dumps({"version": "7.26329.478", "units": [{"factions": [101]}]}).encode()
    other = json.dumps({"version": "7.26329.479", "units": [{"factions": [101]}]}).encode()
    source = tmp_path / "backup.zip"
    with ZipFile(source, "w") as archive:
        archive.writestr("n5/army.json", json.dumps(metadata, indent=2))
        archive.writestr("n5/pan/7.26329.478.json", raw)
        archive.writestr("n5/pan-101/7.26329.478.json", raw)
        archive.writestr("n5/pan/7.26329.479.json", other)
    inventory = tmp_path / "inventory.json"
    write_inventory(inventory_zip(source), inventory)
    direct = tmp_path / "direct.zip"
    with ZipFile(direct, "w") as archive:
        archive.writestr("metadata.json", json.dumps(metadata))
        archive.writestr("101-pan.json", raw)
    manifest = tmp_path / "direct.json"
    provenance = build_snapshot_manifest(
        direct, snapshot_type="army", acquired_at=datetime(2026, 11, 25, tzinfo=timezone.utc),
        source_url="https://api.corvusbelli.com/army", document_count=2,
        project_root=tmp_path, language="en", source_data_changed_on=date(2026, 11, 25),
    )
    manifest.write_text(json.dumps(provenance), encoding="utf-8")
    report = chronology(source, inventory, direct, manifest)
    assert report == chronology(source, inventory, direct, manifest)
    assert report["summary"]["identityStatuses"] == {
        "direct-byte-match": 2, "inferred-folder-and-membership": 1,
    }
    assert report["summary"]["directFactionDocumentsMatched"] == 1
    assert report["summary"]["n5MetadataJsonEqual"] is True
    assert report["summary"]["sameDayUnorderedGroups"] == 1
    observations = report["sequences"][0]["observations"]
    assert len(observations) == 1
    assert observations[0]["sameDayOrder"] == "unknown"
    assert sorted(len(c["members"]) for c in observations[0]["contents"]) == [1, 2]
    bad = inventory_zip(source)
    bad["documents"].pop()
    inventory.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="Inventory does not match"):
        chronology(source, inventory, direct, manifest)
