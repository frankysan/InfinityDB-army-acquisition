# Changelog

All notable user- or operator-relevant changes to Infinity Army acquisition are
documented here. Entries describe meaningful outcomes, with acquisition changes
followed by any operator requirements.

Version 0.1 (package version `0.1.0`) covers this standalone repository from the
split on 2026-11-11. Sections marked **Pre-split (InfinityDB)** record inherited
acquisition work in the [main InfinityDB repository](https://github.com/frankysan/InfinityDB),
not releases of this repository. Their dates identify the original changes.

## [0.1] - Unreleased

### Player summary

No player-facing changes.

### Added

- **Acquisition:** Added the standalone `infinity-army-snapshot` command for
  downloading official Infinity Army metadata and Army lists without installing
  InfinityDB. The package requires Python 3.11 or newer and has no external
  runtime dependencies.
- **Historical acquisition:** Added an offline backup ZIP inventory command for
  N4, N5 and CodeOne faction revision documents and metadata. Reports preserve
  byte identities and validation issues for future unit history research,
  independently of the live snapshot format.
- **Historical acquisition:** Added evidence-qualified faction chronology and
  exact-byte comparison against a verified direct English N5 snapshot. Retains
  ambiguous identities, unordered same-day observations and coverage limits.
- **Historical acquisition:** Added offline Git-object recovery of faction and
  metadata path/blob histories, historical identity candidates and backup
  observation ordering. Supports bare mirrors without working tree checkout.
- **Historical acquisition:** Added Git-backed chronology reconciliation,
  retaining explicit historical identity evidence, byte aliases, metadata
  provenance, and unresolved faction assignments.

### Changed

- **Acquisition:** New downloads default to `local/data/raw/army/` and
  manifests to `local/data/manifests/snapshots/`; explicit legacy paths
  continue to work. Cross-repository transfers remain manual.
- **Acquisition:** Moved Army source acquisition and source-format acceptance
  into this focused repository, retaining the existing response-coherence,
  archive and provenance safeguards. Army normalization, merging, rules and
  database publication remain in InfinityDB.
  ([Standalone extraction](https://github.com/frankysan/InfinityDB-army-acquisition/commit/9a1dee7521dc5c973d7f43b1b7248a42da79b975))

### Fixed

- **Acquisition:** Made matching v3 provenance manifests safe against
  concurrent acquisition runs. New JSON is staged exclusively and published
  without replacing an existing manifest; identical reruns are idempotent.
  Conflicting manifests, symlinks and occupied staging fail closed. No source
  ZIP or manifest format, CLI defaults, or existing evidence was migrated.
- **Acquisition:** Kept acquisition rollback from deleting a competing run's
  identical manifest. Acquisition claims only newly created provenance, while
  direct manifest writes retain idempotent reuse. Equality now checks exact
  bytes, including line endings.

### Upgrade notes

- **Acquisition:** Replaced InfinityDB's former
  `python -m tools.download_army_json` acquisition workflow with the installed
  `infinity-army-snapshot` command. Transfer the immutable ZIP and its matching
  snapshot manifest together; InfinityDB verifies the pair offline with
  `tools.army_snapshot_source.resolve_army_snapshot`. Normal InfinityDB build,
  serve and Docker workflows do not install this package.
- **Acquisition:** The repository contains source code only. Downloaded Army
  data and graphical assets are not included, and the MIT source-code license
  does not cover third-party Army API data.

## 2026-11-11 - Pre-split (InfinityDB)

### Changed

- **Acquisition:** Separated offline verification of an existing Army ZIP and
  its provenance from network acquisition. Consumers can validate a transferred
  snapshot without importing the downloader; this verification remains in
  InfinityDB after the split.
  ([Original change](https://github.com/frankysan/InfinityDB/commit/31b7fc7e50f348c5eb9738386de99543957c1688))

## 2026-09-27 - Pre-split (InfinityDB)

### Changed

- **Acquisition:** Distinguished the latest encoded Army source-change date
  from the time a snapshot was acquired. New Army manifests record both;
  manifest versions 1 and 2 remain readable. Unknown source-revision date
  formats are rejected rather than guessed. The date interpretation is based
  on observed Army revisions, not an upstream documented guarantee.
  ([Original change](https://github.com/frankysan/InfinityDB/commit/171cc92de0501066fa031670495ce2ce180bd738))

## 2026-09-25 - Pre-split (InfinityDB)

### Changed

- **Acquisition:** Made snapshot ZIPs reproducible for identical member paths
  and bytes by standardizing member order, timestamps, permissions and
  compression settings. Added a logical-content hash alongside the exact
  archive hash, allowing content identity to be checked independently of ZIP
  container metadata while retaining support for older manifests.
  ([Original change](https://github.com/frankysan/InfinityDB/commit/86f800f66c06cc059aa4a9f581d88e17229f3588))

### Fixed

- **Acquisition:** Rejected duplicate and case-only colliding archive members
  and invalid member paths during content verification, preventing ambiguous
  snapshot identities across operating systems.

## 2026-09-18 - Pre-split (InfinityDB)

### Added

- **Acquisition:** Added a reusable acquisition operation returning the ZIP,
  matching manifest, acquisition time, language, source URL, document count
  and observed source revisions. Failed provenance publication removes the
  newly created archive so it is not left as a completed snapshot.
  ([Original change](https://github.com/frankysan/InfinityDB/commit/d5cc6521395eec46cf14435f440bc3c0e3af926e))

### Fixed

- **Acquisition:** Added a second request for every metadata and Army-list
  endpoint and compared the response bytes before publishing a snapshot.
  Changed responses fail acquisition without publishing a torn ZIP or
  manifest. Added revision counts to the command output so operators can
  inspect the source revisions contained in a successful snapshot.
  ([Original change](https://github.com/frankysan/InfinityDB/commit/c76765763d5a3d907b8d3f71b6f1d681891adf92))

## 2026-09-17 - Pre-split (InfinityDB)

### Added

- **Acquisition:** Added generated snapshot manifests binding each archive to
  its SHA-256 hash, acquisition time, source URL, language and document count.
  Kept generated acquisition provenance separate from maintained editorial
  notes, and prevented an existing manifest from being overwritten with
  conflicting provenance.
  ([Original change](https://github.com/frankysan/InfinityDB/commit/770b0c90702050e0c0a40236809ad1282c645edb))

### Changed

- **Acquisition:** Standardized timestamped snapshot archives through the
  shared archive writer, preserving exact downloaded bytes and avoiding
  overwrites when multiple snapshots share a timestamp.
  ([Original change](https://github.com/frankysan/InfinityDB/commit/20c94ad2c873c1ec084f0ae5e24022f783eb8ae5))

## 2026-09-10 - Pre-split (InfinityDB)

### Added

- **Acquisition:** Added the manual Army JSON downloader for official metadata
  and one Army-list document per metadata faction, with selectable API
  language and timestamped ZIP output. Source-format validation rejects
  malformed metadata, invalid Unit-list documents and duplicate faction IDs;
  the archived JSON retains the original response bytes. Network requests
  occur only when acquisition is explicitly invoked.
  ([Original change](https://github.com/frankysan/InfinityDB/commit/b88919f3ea48cdc708b5b758453641a6c0434fda))
