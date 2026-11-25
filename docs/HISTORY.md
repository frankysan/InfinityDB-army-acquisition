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

## Reconciled chronology v1

The private main-ref recovery report, at source tip
`0b402cf1bb8aaabe594c67da93bb4e59b049cfbc`, contains 101 Army-related commits,
1,372 faction path/blob pairs and 35 metadata path/blob pairs (14 N4, 13 N5,
8 CodeOne). All archived faction documents match; no additional faction
versions were recovered in this scope. The metadata history adds 32 revisions.

The offline reconciliation binds the original chronology and Git recovery by
their SHA-256 identities and recomputes the comparison before using it. It
preserves prior decisions, evidence and ambiguity, and recomputes sequences
without double-counting exact byte aliases within an edition and faction.
A historical unique folder ID corroborated by membership evidence, or a unique
previously assigned exact-byte alias, supports a new inferred assignment.
Conflicting prior assignments are excluded from sequences rather than silently
overwritten.

Four CodeOne documents with conflicting membership arrays are assigned as
qualified endpoint inferences, not membership confirmations: the downloader
at commits `232df7e614304102a49f5e75e31182d668eeb263` and
`f8962011247fcd88642de4b4b80d6cb635d1bec3` requests each metadata faction ID
and stores responses using its slug. The reviewed main.go blob IDs are
`4f973dbb76ce57fb995b4224c5aeee834239d09a` and
`a844fc9f9f39f266a6e0c9df10c5544902bb2ddd` respectively. The rule is limited
to these observations and the two reviewed folders, Combined Army (10601)
and Nomads (10501). CodeOne memberships do not determine endpoint identity.

The same historical slug and membership evidence supports three N4 Winterfor
documents (106); the exact-byte alias to the later suffixed folder supports one
N5 Contracted Back-up assignment (998). The source downloader at
`825fde0c9f58e0d1846db7de94b9d63281d04255` (main.go blob
`05f961293a8713a2b495b665fcc9e12e14308447`) explicitly disambiguates duplicate
slugs by appending the faction ID. Earlier unsuffixed filenames cannot generally
identify which endpoint supplied a document; retain 15 unresolved observations
(7 N4, 8 N5). Do not extrapolate from the one exact-byte match.

Result: 1,357 assigned documents (58 direct matches, 1,299 inferred), 119
edition-specific faction sequences and 1,355 distinct assigned faction contents.
113 same-day groups have distinguishable first-parent backup ordering and four
remain unordered. All upstream within-day publication ordering remains unknown.
The report retains the historical metadata references, not a replacement for
the original Git objects. It does not yet constitute a consumer handoff.

## Historical source archive v1

The private archive stores each exact document byte sequence once, at
`objects/sha256/<sha256>.json`. The index records each source observation
independently (backup ZIP member, Git path/blob pair or direct API ZIP member),
its edition, byte identity, source revision where known, and faction ID or
unresolved identity status. Git observations retain commit and historical
metadata-blob references; direct observations retain their snapshot identity,
acquisition time and metadata SHA-256. Duplicate source observations are not
duplicate changes. Metadata objects are preserved as raw bytes, not recreated
from their extracted faction rows.

The builder recomputes chronology and reconciliation, checks each selected
direct v3 snapshot, and, when supplied a local mirror, recomputes the pinned
Git recovery. Each Git object is checked against its blob ID and SHA-256.
The original inventory, chronology, recovery, reconciliation and selected
direct manifests are embedded unchanged as hashed evidence. Additional direct
English N5 snapshot pairs may be selected without changing the historical
reconciliation. Their independently identified faction observations remain
separate; this stage does not extend the reconciled sequences automatically.
The embedded reconciled chronology is the source of its existing sequence
assignments and backup ordering. No new unit identities or semantic changes
are derived.

The archive is deterministic for fixed inputs and the same ZIP implementation.
It is verified before exclusive publication. The standalone verifier checks
internal member sets, byte hashes, evidence hashes, reference integrity and
summary consistency; it does not authenticate an independently untrusted
index or replace the original input checks. An external archive SHA-256
identifies the finished artifact. Completeness means all referenced bytes
for the selected inputs exist, not full historical or release coverage.
Partial builds require explicit opt-in, enumerate missing hashes and sizes,
and return exit code 2; strict verification rejects them. Retain the mirror
and original sources separately.

The 2026-11-25 partial real-source build retained 2,841 source observations,
1,374 unique available objects (1,370 faction, four metadata) and 32 missing
historical metadata objects. The 30 unresolved faction observations are the
same 15 ambiguous documents recorded in two independent source inventories.
The external mirror path is rejected by MCP (script_path_escape); completing
the selected-input archive requires running the documented mirror command
locally. The complete path is tested with a synthetic bare repository.
No private archive, report or downloaded document is committed or published.

## Subsequent work

The complete real-source archive has now passed strict verification with 1,406
unique objects, zero missing objects, and 2,841 observations. The producer
handoff acceptance also resolved every Git and direct metadata context.
See [historical source handoff](HISTORY_HANDOFF.md) for the pinned candidate
interface, exact archive identity, downstream responsibilities and outstanding
consumer acceptance gate.

1. Transfer the selected archive and acceptance receipt explicitly and validate
   an independent InfinityDB reader against the candidate contract.
2. Review additional historical refs (including n4-checkpoint) and independent
   direct acquisitions, where useful for remaining ambiguous observations.
3. Derive semantic unit histories in InfinityDB. Do not publish or change the
   consumer in this project. Complete reconstructed snapshots remain secondary.

Live API acquisition and its two-pass acceptance contract remain unchanged.
