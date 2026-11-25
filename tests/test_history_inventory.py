import hashlib
import json
from zipfile import ZipFile

import pytest

from infinity_army_acquisition.history_inventory import inventory_zip, main, write_inventory


def make_zip(tmp_path, members):
    path = tmp_path / "source.zip"
    with ZipFile(path, "w") as archive:
        for name, raw in members:
            archive.writestr(name, raw)
    return path


def document(version="7.26329.478"):
    return json.dumps({"version": version, "units": [{"id": 1}]}).encode()


def test_inventory_tracks_editions_bytes_dates_and_metadata(tmp_path):
    raw = document()
    source = make_zip(tmp_path, [
        ("backup/n5/panoceania/7.26329.478.json", raw),
        ("backup/n4/panoceania/7.26329.478.json", raw),
        ("backup/codeone/aleph/7.26329.478.json", raw),
        ("backup/n5/army.json", b'{"factions": []}'),
        ("backup/n5/panoceania/panoceania.json", raw),
        ("backup/n5/panoceania/units/unit.json", b"ignored"),
    ])
    report = inventory_zip(source)
    assert report == inventory_zip(source)
    assert report["source"]["archiveSha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert report["source"]["commit"] is None
    assert report["source"]["coherence"] == "unverified"
    assert report["summary"]["documents"] == 4
    assert report["summary"]["duplicateByteContents"] == 2
    assert report["summary"]["documentsWithIssues"] == 0
    for edition in ("n4", "n5", "codeone"):
        assert report["summary"]["editions"][edition]["factionDocuments"] == 1
    row = next(row for row in report["documents"] if row["kind"] == "faction")
    assert row["sha256"] == hashlib.sha256(raw).hexdigest()
    assert row["encodedRevisionDate"] == "2026-11-25"
    assert row["unitCount"] == 1


def test_invalid_rows_preserved_and_cli_reports_issues(tmp_path):
    source = make_zip(tmp_path, [
        ("n5/one/7.26329.478.json", document("7.26329.479")),
        ("n5/two/7.26367.1.json", document("7.26367.1")),
        ("n5/three/7.26329.478.json", b"not json"),
    ])
    output = tmp_path / "report.json"
    assert main([str(source), "--output", str(output)]) == 2
    report = json.loads(output.read_bytes())
    assert report["summary"]["documentsWithIssues"] == 3
    assert {issue for row in report["documents"] for issue in row["issues"]} == {
        "filename-revision-mismatch", "unknown-revision-date", "invalid-source-shape"
    }
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        write_inventory(report, output)
    assert output.read_bytes() == before


@pytest.mark.parametrize("members", [
    [("n5/one/7.26329.478.json", document()), ("n5/One/7.26329.478.json", document())],
    [("a/n5/one/7.26329.478.json", document()), ("b/n5/two/7.26329.478.json", document())],
    [("n5/../7.26329.478.json", document())],
    [("n5/one/units/unit.json", document())],
])
def test_reject_ambiguous_or_empty_archive(tmp_path, members):
    with pytest.raises(ValueError):
        inventory_zip(make_zip(tmp_path, members))
