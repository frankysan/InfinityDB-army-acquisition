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
hashes. Unknown source-revision date formats are rejected.

For use by InfinityDB, transfer the immutable ZIP and its matching
manifest. InfinityDB validates the pair offline with
tools.army_snapshot_source.resolve_army_snapshot. The normal
InfinityDB build/serve/Docker workflows do not install this package.

Only source-facing acceptance is copied here; importing or running
InfinityDB's data model and normalization is not required.
