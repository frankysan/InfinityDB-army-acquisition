# Development and integration

This is the canonical development guide for the standalone Army API producer.
[AGENTS.md](../AGENTS.md) is the agent entry point; the [README](../README.md)
defines its public CLI and current source handoff, while
[pyproject.toml](../pyproject.toml) and
[the test workflow](../.github/workflows/tests.yml) define actual packaging
and CI checks. The [changelog](../CHANGELOG.md) records meaningful
operator-facing changes, not routine internal refactoring.

## Ownership and source contracts

- **Acquisition:** Query the official Army metadata and corresponding Army-list
  documents. Validate the source shape, unique faction identities and expected
  document set without normalizing their gameplay meaning.
- **Coherence:** Keep the two-request byte comparison for every endpoint. A
  changed response, malformed member, colliding archive path, failed write or
  unknown source-revision-date encoding must not publish a complete snapshot.
- **Artifacts:** Preserve original JSON response bytes in a deterministic
  timestamped ZIP; write its matching v3 provenance manifest. Keep exact
  archive SHA-256 separate from logical-content SHA-256 and source-data-change
  date separate from acquisition time. Never overwrite a previous identity.
- **Consumer:** InfinityDB verifies the immutable ZIP/manifest pair offline
  using `tools.army_snapshot_source.resolve_army_snapshot`. Merging, identity
  resolution, curated rules, generated databases and browser publication
  belong to InfinityDB; this package must not depend on those modules.
- **Historical recovery:** Follow [historical acquisition](HISTORY.md).
  Document-level preservation for unit history is primary; recovered source
  evidence is not equivalent to a directly validated live snapshot.

A producer contract change requires a versioned input/output example, review
of legacy-reader behavior, source-format tests, a matching consumer-verifier
test at a **pinned InfinityDB revision**, and explicit migration guidance.
Do not rewrite a consumer's source note or infer authority from a producer
hash. A successful ZIP download does not certify gameplay data accuracy.

## Implementation and validation

Python 3.11+; installed package with no external runtime dependencies.
From this repository root, in the selected virtual environment:

```powershell
python -m pip install -e ".[test]"
python -m pip check
python -m pytest -q
```

Keep the default suite hermetic: mocked HTTP responses and temporary ZIPs
only, with no live API, private snapshots or sibling checkout. Extend focused
tests for successful archive/manifest round trips and negative paths:
inconsistent responses, malformed payloads, unsafe/duplicate/case-colliding
members, invalid dates, incomplete publication and source-hash mismatch.
The hosted workflow runs these checks on Windows, Ubuntu and macOS with
Python 3.11. Report the local result separately from hosted CI status.

Live `infinity-army-snapshot` acquisition is a deliberate, networked
operator action. Its new defaults target the standalone checkout's
`local/data/raw/army/` and `local/data/manifests/snapshots/`; the old
`data/raw` and `data/manifests/snapshots` destinations remain supported
with explicit CLI arguments. Paths are ignored and not packaged. Transfer
reviewed pairs to InfinityDB explicitly, without changing manifest bytes.
For **new** ignored research, validation, private handoffs and scratch,
use descriptive categorized `local/data/`, `local/research/`,
`local/validation/`, `local/handoffs/` or `local/work/` destinations.
Include domain/purpose/input revision or run ID; do not overwrite existing
run evidence. Do not move pre-existing ignored snapshots without a
consumer, backup/restore and provenance review.

## Documentation and lifecycle

- All agents must record concrete improvement opportunities in the
  [agent improvement log](AGENT_IMPROVEMENTS.md), including out-of-scope
  ideas. Follow its evidence, deduplication and status requirements. The
  log collects suggestions; it does not authorize work or replace an
  approved task plan.
- Update the README for changed CLI, supported source shape or handoff;
  this guide for developer/check policy; code/tests for executable
  guarantees; and the changelog for meaningful operator consequences.
- Keep one current owner per contract. Mark proposals and historical
  evidence explicitly; do not duplicate a main InfinityDB backlog, release
  checklist, VD/VR register or multi-agent protocol here.
- For a one-use acquisition investigation/tool, name its purpose, scope,
  input revision, evidence and retirement trigger. At closeout, inspect
  independent consumers; preserve still-needed facts and source provenance,
  then remove superseded scripts/reports with historical-only tests rather
  than accumulating an `archive/` tree.
- Original third-party Army data is not licensed under this repository's
  MIT source-code license. Keep acquisitions and machine-specific evidence
  ignored/private with separate backups as needed. Git ignore is not an
  access or backup mechanism.

Work in this producer does not implicitly update InfinityDB, deploy the
application, synchronize another repository or certify the downstream
runtime. Handoffs state format version, exact ZIP and manifest identity,
producer Git SHA, relevant source revisions and separately observed
consumer verification.
