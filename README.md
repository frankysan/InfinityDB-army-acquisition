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

    infinity-army-snapshot data/raw --language en --manifest-dir data/manifests/snapshots

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
