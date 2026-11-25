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

## Faction chronology v1

The offline chronology checks the inventory against a fresh source scan,
validates both archive and logical hashes of a supplied direct English N5 v3
snapshot, then compares individual faction response bytes. The operator must
select an N5 direct snapshot; the existing manifest does not encode edition.
A unique direct byte match anchors the upstream faction ID. Otherwise, the
intersection of all units' nonempty integer faction-membership arrays and the
edition's retained metadata slug (including slug-ID folders) support an
inferred assignment. Partial membership coverage is explicitly distinguished
from full coverage; absent evidence never becomes a confirmed identity. A
unique common membership ID in retained metadata may support a renamed folder
only with full coverage. CodeOne membership IDs use a different namespace
from its metadata: same-slug N4 metadata and common memberships can corroborate
a CodeOne folder ID without merging editions. Conflicting or ambiguous evidence
remains unresolved. These are source faction hypotheses, not canonical app
identities; retained metadata may be newer than the historical document.

Sequences are edition- and source-ID-scoped, grouped by encoded date. Within a
date, distinct byte hashes are unordered; exact duplicate bytes preserve every
member path. Inter-observation days measure spacing, not missing release counts.
Direct matches, unmatched direct documents, membership evidence and unresolved
archive documents are retained. The report is research evidence, not a new
snapshot or consumer contract. No semantic unit changes are derived here.

## Observed validation (2026-11-25)

The local backup ZIP inventory contains 1,372 faction responses. Comparing the
English N5 acquisition dated 2026-11-25 against that backup produced 58/58 exact
faction byte matches and equal parsed metadata. Chronology assigned 1,349
responses (58 direct matches, 1,291 inferred); 23 remain unresolved, including
16 under the historically colliding contracted-back-up folder, three N4
winterfor documents and four CodeOne documents. The 117 same-day unordered
groups require further evidence before deriving within-day changes. The private
report retains all observations and hashes. The standalone pytest execution
route remains blocked through MCP (AI-0003); run the repository suite locally.

## Git-backed recovery v1

Select a local complete Git repository (ordinary or bare), branch ref or exact
commit. Git recovery pins that tip and scans the selected first-parent history
of N4, N5 and CodeOne paths. It does not fetch, checkout or mutate the source.
Shallow repositories are rejected. Other refs and non-first-parent branch
history need separate review; this is not an exhaustive all-ref inventory.

Recover each version-named faction path/blob pair and each edition's
`army.json` path/blob pair, including ones no longer at the tip. Preserve Git
object IDs, exact byte SHA-256, size, encoded source revision, commit ID,
committer timestamp, first observation and subsequent reappearances. Record
path removals and replacements, contemporaneous metadata blob and metadata
faction rows. The original full bytes remain recoverable by Git blob ID; this
report is not a replacement for the mirror.

Compare against the existing v1 chronology by relative Army path and exact
SHA-256, retaining both source identities. A unique contemporaneous metadata
folder mapping, possibly corroborated by an exact-byte alias, is a **candidate**
for previously unresolved identities. Conflicting candidate IDs are not
accepted and previous assignments are not overwritten. A candidate is not an
endpoint confirmation; historical downloader behavior, unit membership evidence
and possible ID reuse still need review.

For same-day groups, distinct first-observed first-parent commits establish
an ordering of backup observations only. A tie, missing match or same commit
remains unordered; upstream release order is always unknown at this stage.
Commit timestamps are backup evidence, not source release timestamps.
No unit change events or complete snapshot reconstructions are produced.

The synthetic Git fixture covers a bare mirror, historical metadata changes,
removed paths, exact-byte aliases and same-day observation ordering. Run the
full private mirror scan explicitly from the checkout, then review proposed
identities and any unresolved or conflicting observations. The mirror is not
directly accessible through the current Git-scoped MCP workspace interface.

## Subsequent work

1. Execute Git recovery on the local mirror and review proposed historical
   faction IDs, same-day evidence and any additional historical refs.
2. Preserve each distinct source document with provenance and explicit
   chronology gaps; identify possible complete snapshots as secondary outputs.
3. Define a versioned downstream handoff with InfinityDB, then derive semantic
   unit histories there. Do not publish or change the consumer in this project.

Live API acquisition and its two-pass acceptance contract remain unchanged.
