# Historical Army acquisition

## Objective

The primary downstream objective is an evidence-backed unit version history in
InfinityDB: observed additions, removals and modifications to units, profiles,
loadouts, costs, faction availability and other gameplay-relevant fields.

This producer preserves document-level history first. Complete reconstructed
snapshots are optional and must not be a prerequisite for retaining useful
individual revisions. InfinityDB owns canonical identities, semantic differences,
cross-faction reconciliation and player-facing history. Do not infer those here.

## Source and first inventory

The secondary source is the community
[massayoshi/infinity-army-backup](https://github.com/massayoshi/infinity-army-backup)
archive. It retains version-named faction documents and pretty-printed metadata.
The source author describes personal-use backup; retain the archive and generated
inventory privately. Public redistribution is not authorized by this workflow.

Inventory v1 reads a supplied ZIP directly, without extracting files, running
third-party code or making network requests. It selects N4, N5 and CodeOne
edition metadata and numeric three-component version-named faction documents;
it excludes pretty-printed faction aliases, individual unit exports, images and
Wiki files. Its source identity is the exact ZIP SHA-256 and member path; a ZIP
alone does not prove a Git commit, original HTTP bytes or a coherent acquisition.
The language is attributed to the backup's English configuration convention,
not independently detected from every document.

For each document retain byte hash, byte length, edition, archive member,
folder label, filename and embedded revision, inferred encoded revision date,
unit count where available and validation issues. Unknown dates and malformed
or mismatched responses remain visible as evidence but are not accepted as
valid chronology. Exact duplicate bytes share a hash; no source is deleted.
Folder names are not canonical faction identities. A matching revision string
does not establish byte equality, and same-day revisions have no assumed order.

The report is deterministic for a fixed input ZIP, and separate from the v3
live-snapshot manifest. It is an inventory, not a consumer-ready snapshot.
Do not infer introduction dates from earliest observations, exact publication
times from encoded dates, or absence from incomplete source coverage.

## Subsequent work

1. Validate the full archive and compare original bytes to direct acquisitions.
2. Recover Git blob and commit provenance and historical metadata from the bare
   mirror without a working tree. Investigate renamed and colliding faction
   folders and derive source faction identities from contemporaneous evidence.
3. Preserve each distinct source document with provenance and explicit
   chronology gaps; identify possible complete snapshots as secondary outputs.
4. Define a versioned downstream handoff with InfinityDB, then derive semantic
   unit histories there. Do not publish or change the consumer in this project.

Live API acquisition and its two-pass acceptance contract remain unchanged.
