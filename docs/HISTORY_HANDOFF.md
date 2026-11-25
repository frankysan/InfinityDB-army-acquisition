# Historical Army source handoff — v1 candidate

Status: producer-side contract and acceptance only; InfinityDB consumer implementation
and acceptance remain pending. This is a separate historical input, not a live Army
snapshot or a replacement for the current runtime data set.

## Selected source and transfer

Select an immutable complete historical archive and its independently supplied
SHA-256 explicitly. The current reference artifact was built at producer revision
`8f14ca64c2bcd2ecee5e61a06f155792b5d873d4`:

- Basename: `army-history-v1.zip`.
- SHA-256: `08978b9bbf3fffa3184f6153fa4dd05a1931482742f08ee5de7a6df4f4a3c5c5`.
- Format: `InfinityDB historical Army source archive`, formatVersion 1.
- Backup Git tip: `0b402cf1bb8aaabe594c67da93bb4e59b049cfbc`, main first-parent Army path history.
- Direct English N5 snapshot: `JSON 20261125-162328.zip`, SHA-256
  `8e2c53fc3425ab80627ba99c88629bc33df6403971465ba1fcccef7882da0715`.
- 1,406 objects, 2,841 observations, 119 assigned edition/faction sequences,
  1,355 assigned edition/faction/date/content combinations, 15 unresolved
  edition/content combinations, 36 metadata objects, zero missing objects.

Transfer the selected archive unchanged and the separately generated acceptance
receipt privately into an explicitly selected ignored source directory, proposed
`local/data/history/archive/` on the consumer. Verify the expected digest out of
band; a receipt stored alongside an untrusted archive is not authentication.
Never place this ZIP in `local/data/raw/army/`, use latest-snapshot discovery,
publish the ZIP to the browser, or introduce a runtime dependency on local research
inputs. A subsequent acquisition is a new explicitly pinned artifact, not an
in-place update.

## Format and reader

Read `index.json` and the exact member set, without filesystem extraction.
Require formatVersion 1, completeForSelectedInputs true, empty missingObjects,
object SHA-256 and byte-size matches, evidence SHA-256 matches and exact reference
coverage. Reject unknown versions, malformed content, unexpected or colliding
members, wrong external hash and partial archives. Pin all source/evidence inputs
in build provenance. The producer acceptance receipt is useful comparison evidence,
not a substitute for the consumer implementing its own reader.

Each `objects/sha256/<sha256>.json` member is original document bytes. Objects are
not units or events. Index observations contain:

| Field | Interpretation |
|---|---|
| sourceType | backup-zip, backup-git, direct-api |
| edition, kind | n4/n5/codeone; faction/metadata |
| sha256, sizeBytes | exact object identity and size |
| factionId, identityStatus | source endpoint hypothesis or null; direct-endpoint and direct-byte-match have stronger evidence than inferred statuses |
| sourceRevision, encodedRevisionDate | faction document version and decoded date; metadata has no such date |
| member, sourceArchiveSha256 | ZIP observation locator and source archive identity |
| path, blob, sourceTipCommit | Git path/blob observation identity |
| firstObservation, appearances | Git commits, commitIndex, committedAt and metadataBlob for observation context |
| acquiredAt, metadataSha256 | direct acquisition timestamp and associated metadata object |

Fields are source-specific; absent values must not be inferred from a different
source type. Preserve the original evidence reports and unresolved observations.
Use Git metadata links by edition/blob, direct metadata links by snapshot SHA-256,
and exact object references. A contemporaneous Git metadata tree is observation
context, not proof it was the metadata at the upstream publication instant.
Do not borrow today's metadata to silently interpret older numeric identifiers.

Example of a synthetic historical faction observation (hash abbreviated only for
documentation; actual hashes must be complete):

    edition: n5
    factionId: 101
    sourceType: backup-git
    sourceRevision: 7.26329.478
    encodedRevisionDate: 2026-11-25
    identityStatus: inferred-folder-and-membership
    sha256: <64 lowercase hex characters>

One document can have several observations. Deduplicate comparison inputs by
(edition, source faction ID, encoded date, SHA-256), preserving the observations.
Keep uncertain assignments out of assigned comparisons. Retain all distinct
same-day contents; embedded reconciled sequence order is backup observation
order only. Do not infer upstream publication order from commit time, revision
suffix or lexical order. Direct acquisitions added after reconciliation must
also enter the comparison input grouping; the embedded reconciled sequence
alone is not the full archive inventory.

## Downstream work (InfinityDB-owned)

Reviewed against InfinityDB dev/v1.2.1 at
`7d6fffab924f5f7bd94df73d555ce9be62a69dce`:

- `src/infinity_db/army_snapshot_source.py` verifies a single direct snapshot and
  matching manifest (legacy v1/v2 and strict v3). Historical archives are not
  accepted inputs for this reader. `tools/data/army_snapshot_source.py` is a facade.
- `src/infinity_db/database_set_builder.py` pins the current source and maintained
  input fingerprints. Keep that current-data contract unchanged.
- `docs/data-model.md`, Logical Units and Army identities, owns source-to-logical
  mappings and contextual profile/loadout semantics. Source IDs alone are not
  canonical identities, particularly across editions.
- `docs/architecture.md` and `data/README.md` require immutable inputs, explicit
  input fingerprints, separate generated data, no implicit acquisition or
  dependence on private local data at runtime.

Recommended initial consumer scope: an independent offline historical source
reader, evidence inventory and edition/faction-scoped normalized comparison
pilot for N5, preserving all other editions for later processing. Do not select
a runtime database schema or alter release scope in this producer. Then resolve
historical logical Unit identity with reviewed/source-derived mappings, normalize
profile/loadout structure and catalog references against contextual metadata,
classify gameplay-relevant differences, and reconcile cross-faction duplicates.
Keep actual changes distinct from formatting, order, source ID churn and unknown
semantics. Label first/last observation as such, not introduction/removal dates;
report change bounds and faction scope, and preserve uncertainty across gaps.
Public display, database placement, source rights and release acceptance require
separate InfinityDB decisions. No third-party archive redistribution is authorized.

## Acceptance gate

Producer acceptance command:

    python -m tools.history_handoff local/data/history/archive/army-history-v1.zip --sha256 08978b9bbf3fffa3184f6153fa4dd05a1931482742f08ee5de7a6df4f4a3c5c5 --output local/data/history/archive/army-history-v1.acceptance.json

The producer checks strict archive integrity, embedded evidence linkage,
source-version/encoded-date consistency, reviewed faction assignments,
metadata reference integrity and edition/faction/date/content grouping.
The receipt records `consumerAcceptance: not-tested` deliberately.

At the pinned consumer revision, the existing reader requires a matching
snapshot manifest, one metadata.json, direct snapshot revision counts and
supported source dates. The historical ZIP has a different index and member
set, so it must not be routed through the old reader. The existing legacy
reader remains unchanged. Consumer acceptance requires an independently
implemented separate reader, hermetic positive and negative tests (wrong
hash, incomplete archive, missing/corrupt objects, unsupported version,
ambiguous identity, same-day order), and matching real-source counts/context
references above. Preserve existing snapshot tests and run a focused offline
consumer test batch at the actual implementation commit. No consumer reader
or test is currently implemented in this task; the integration gate is pending.
