import json

import pytest

from infinity_army_acquisition import cli as module


@pytest.mark.parametrize("collision", ["identical-manifest", "different-manifest", "archive"])
def test_manifest_race_preserves_other_acquisition_output(
    tmp_path, monkeypatch, collision,
) -> None:
    from infinity_army_acquisition import snapshot_provenance as provenance

    def download(staging, **_kwargs):
        metadata = staging / "metadata.json"
        faction = staging / "101-test.json"
        metadata.write_text("{}", encoding="utf-8")
        faction.write_text('{"version":"7.26246.158","units":[]}', encoding="utf-8")
        return [metadata, faction]

    link = provenance.os.link
    winner = b""
    target = None

    def competing_link(source, destination):
        nonlocal winner, target
        target = destination
        winner = source.read_bytes() if collision == "identical-manifest" else b"other acquisition\n"
        destination.write_bytes(winner)
        link(source, destination)

    monkeypatch.setattr(module, "download_snapshot", download)
    if collision == "archive":
        from pathlib import Path

        original_zip = provenance.zipfile.ZipFile

        def competing_zip(path, mode="r", **kwargs):
            nonlocal target, winner
            if mode == "x":
                target = Path(path)
                winner = b"other acquisition's source ZIP"
                target.write_bytes(winner)
            return original_zip(path, mode, **kwargs)

        monkeypatch.setattr(provenance.zipfile, "ZipFile", competing_zip)
    else:
        monkeypatch.setattr(provenance.os, "link", competing_link)
    with pytest.raises((provenance.SnapshotProvenanceError, FileExistsError)):
        module.acquire_army_snapshot(
            tmp_path / "raw", tmp_path / "manifests", project_root=tmp_path,
        )
    assert target is not None and target.read_bytes() == winner
    assert list((tmp_path / "raw").glob("*.zip")) == ([target] if collision == "archive" else [])
    assert not list((tmp_path / "manifests").glob("*.tmp"))


def load_module():
    return module


def test_filename_slugifies_bad_faction_names() -> None:
    module = load_module()

    name = module._filename({"id": 42, "slug": "Special: Recent/Changes?*"})
    assert name == "42-special-recent-changes.json"


def test_main_writes_snapshot_provenance_and_reports_revisions(
    tmp_path, monkeypatch, capsys
) -> None:
    module = load_module()
    destination = tmp_path / "raw"
    manifest_directory = tmp_path / "manifests"

    def fake_download(staging, *, language, **_kwargs):
        metadata = staging / "metadata.json"
        army = staging / "101-panoceania.json"
        sectorial = staging / "102-sectorial.json"
        metadata.write_text("{}", encoding="utf-8")
        army.write_text(
            json.dumps({"version": "7.26246.158", "units": []}),
            encoding="utf-8",
        )
        sectorial.write_text(
            json.dumps({"version": "7.26246.159", "units": []}),
            encoding="utf-8",
        )
        return [metadata, army, sectorial]

    monkeypatch.setattr(module, "download_snapshot", fake_download)

    assert (
        module.main(
            [
                str(destination),
                "--manifest-dir",
                str(manifest_directory),
            ]
        )
        == 0
    )

    archives = list(destination.glob("JSON *.zip"))
    manifests = list(manifest_directory.glob("*.json"))
    assert len(archives) == 1
    assert len(manifests) == 1

    from infinity_army_acquisition.snapshot_provenance import load_snapshot_manifest

    document = load_snapshot_manifest(manifests[0], archive=archives[0])
    assert document["snapshot"]["type"] == "army"
    assert document["snapshot"]["documentCount"] == 3
    assert document["source"] == {
        "dataChangedOn": "2026-09-03",
        "language": "en",
        "url": module.API_BASE_URL,
    }

    output = capsys.readouterr().out
    assert "Downloaded 2 army lists and metadata" in output
    assert "Army source revisions -> 7.26246.158: 1, 7.26246.159: 1" in output
