# Infinity Army acquisition

Standalone downloader for the official Infinity Army API. This
repository owns only source acquisition and source-format acceptance.
Army normalization, merging, rules and database publication remain
in the separate InfinityDB repository.

No downloaded source data or graphical assets are stored in this
repository. The MIT source-code license does not cover third-party
Army API data.

## Installation and offline tests

Python 3.11 or newer; no external runtime dependencies.

    python -m pip install -e ".[test]"
    python -m pytest -q

Tests use mock API responses and local temporary ZIPs only.

## Manual acquisition

    infinity-army-snapshot --language en

By default, immutable ZIPs are written under `local/data/raw/army/`
and matching manifests under `local/data/manifests/snapshots/`, relative
to the directory from which the command is invoked. The previous destinations
remain available explicitly:

    infinity-army-snapshot data/raw --manifest-dir data/manifests/snapshots

This is the producer repository's own `local/` workspace. Transfer selected
ZIP/manifest pairs to InfinityDB's equivalent paths explicitly; the two
repositories do not share files or synchronize automatically.

The downloader validates each endpoint and repeats every request.
Different response bytes between passes fail closed; no torn snapshot
ZIP or manifest is published. It creates a timestamped JSON ZIP and
version-3 snapshot provenance with exact archive and logical-content
hashes. Unknown source-revision date formats are rejected. Manifest
publication is no-clobber: a previously written manifest is reusable only
when its complete canonical JSON bytes match. New manifests are staged
exclusively and published through same-directory hard-link creation;
a competing acquisition cannot replace different provenance. Stale
`.json.tmp` files and symlink destinations cause an error rather than being
overwritten. Inspect interrupted staging before removing it. The selected
filesystem must support hard links; no overwriting fallback is used.

The acquisition transaction requires a newly created manifest, even if a
competing run publishes identical bytes. This keeps rollback from deleting
another run's output. Direct `write_snapshot_manifest` callers retain
idempotent reuse by default; CRLF and LF are different byte identities.

For use by InfinityDB, transfer the immutable ZIP and its matching
manifest. InfinityDB validates the pair offline with
tools.army_snapshot_source.resolve_army_snapshot. The normal
InfinityDB build/serve/Docker workflows do not install this package.
Keep the original ZIP and manifest basenames. The optional producer-relative
`snapshot.archive.path` is informational: explicitly select the transferred
archive without rewriting its manifest or resolving that path on the receiver.

Only source-facing acceptance is copied here; importing or running
InfinityDB's data model and normalization is not required.

## Historical acquisition

The primary downstream goal is evidence-backed unit version history.
See [historical acquisition](docs/HISTORY.md) for scope and provenance.
Inventory a private backup ZIP offline (no working tree needed):

    python -m infinity_army_acquisition.history_inventory local/infinity-army-backup.zip --output local/data/history/inventory/backup-v1.json

The equivalent installed command is `infinity-army-history-inventory`.
The repository workspace adapter `python -m tools.history_inventory` accepts
exactly the same arguments for bounded agent execution.
It writes a new deterministic inventory of versioned faction documents and
metadata, never a live snapshot. Exit 0 means all selected documents passed
basic validation; 2 means a report was written with document issues; 1 means
the inventory could not be completed or published.

Group the archived documents into evidence-qualified faction sequences and
compare them with a verified direct English N5 snapshot:

```powershell
python -m tools.history_chronology local/infinity-army-backup.zip `
    --inventory local/data/history/inventory/backup-v1.json `
    --direct "local/data/raw/army/JSON 20261125-162328.zip" `
    --manifest "local/data/manifests/snapshots/JSON 20261125-162328.json" `
    --output local/data/history/chronology/backup-v1-new.json
```

The chronology is a separate v1 research report. It retains unresolved
identities and same-day ambiguity; it does not claim complete history or
introduce gameplay change events.
