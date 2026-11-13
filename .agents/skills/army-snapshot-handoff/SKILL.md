---
name: army-snapshot-handoff
description: "Domain-specific procedure for army snapshot and consumer handoff in InfinityDB-army-acquisition; use for source, provenance and cross-repository contract changes."
---

# Army snapshot and consumer handoff

## Use this workflow when

- Changing Army API fetches, validation, archive layout, revision parsing or provenance.
- Updating a snapshot producer field consumed by InfinityDB.

## Procedure

1. Read [development guidance](../../../docs/DEVELOPMENT.md) and the [README](../../../README.md); inspect current `src/` producers and corresponding tests.
2. Name the exact upstream endpoint(s), language, source revision and response/ZIP members. Distinguish acquisition time from the encoded source-data-change date.
3. Preserve source bytes and enforce the two-request coherence check. Treat missing factions, changed responses, duplicate/case-colliding paths, unrecognized dates and partial writes as explicit failures.
4. Keep deterministic ZIP byte identity, logical-content hash and exact archive hash independently testable. Do not normalize Army semantics or edit the consumer database.
5. When a handoff changes, pin the consuming InfinityDB commit and compare the `resolve_army_snapshot` contract, including legacy manifests and negative mismatches. A producer success alone does not pass this downstream gate.
6. Add focused hermetic source-format and artifact tests; run the standalone pytest suite and record any consumer test that remains blocked with its exact revision/input and trigger.
7. Update the README for operator-visible CLI changes and the changelog for substantive outcomes. Report producer SHA, source/format versions, actual checks, input/output identity and unresolved downstream work.

Do not acquire live data, publish raw Army artifacts, or modify sibling repositories without explicit authorization.
