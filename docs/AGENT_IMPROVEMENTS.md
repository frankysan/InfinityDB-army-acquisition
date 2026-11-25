# Agent improvement log

This is the single collection point for concrete potential improvements to
code, tests, tooling, workflows and agent instructions in this repository.
All coding, research and documentation agents must record opportunities
they identify, including ideas outside the current assignment.

An entry is a suggestion. Recording it does not authorize implementation,
expand the current task, or replace an approved task plan or source evidence.
Do not investigate unrelated work merely to populate this log.

## Required agent behavior

1. Record actionable opportunities as they arise during implementation,
   investigation, testing, documentation review or handoff. Give a concrete
   reason; distinguish observed facts from hypotheses and unknowns.
2. Check existing entries first. Update a matching entry rather than
   duplicating it. Assign each new entry the next unused `AI-####` ID and
   keep that ID stable.
3. Include the date, affected files or instructions, supporting observations
   or reproduction steps, proposed improvement, expected benefit and status.
   Do not invent evidence or include secrets, private source material or
   machine-specific private paths.
4. Continue the authorized task. Implement an improvement only when it is
   already within scope or separately authorized; otherwise record it as
   `proposed` or `deferred`.
5. Update the status when an idea is accepted, implemented, deferred,
   declined or superseded. Link the relevant task, commit or decision when
   available and retain the history. Mention relevant new entries in the
   final handoff without presenting suggestions as completed work.

If the checkout is read-only or this document cannot be updated, include the
proposed entry in the handoff for later recording. Do not modify another
repository merely to capture an idea.

## Entry format

Use one improvement per entry:

```markdown
### AI-#### — Short title

- **Date:** YYYY-MM-DD
- **Status:** proposed | deferred | accepted | implemented | declined | superseded
- **Affected files or instructions:** Repository-relative paths or named rules.
- **Observations:** Supporting evidence or reproduction steps; identify any
  hypotheses and unknowns explicitly.
- **Proposed improvement:** Concrete change and relevant trade-offs.
- **Expected benefit:** Why the change would help; label unmeasured benefits.
- **Disposition:** Next step, reason deferred, or linked task/commit/decision.
```

## Entries

### AI-0001 — Make improvement recording explicit in repository guidance

- **Date:** 2026-11-17
- **Status:** implemented
- **Affected files or instructions:** `AGENTS.md`, `docs/DEVELOPMENT.md`,
  `docs/AGENT_IMPROVEMENTS.md`.
- **Observations:** The repository agent instructions and development guide
  did not designate an improvement log or state its recording requirements.
  InfinityDB-products provides an explicit instruction and dedicated log;
  the user requested the same general agent behavior here.
- **Proposed improvement:** Designate this document and require dated,
  evidence-backed entries, deduplication, status updates and preservation
  of task boundaries.
- **Expected benefit:** Future agents can find and assess suggestions
  without relying on conversation history. This benefit is unmeasured.
- **Disposition:** Implemented by the accompanying documentation change,
  following the user's instruction. No code or acquisition contracts changed.

### AI-0002 — Add an advisory update check using endpoint ETags

- **Date:** 2026-11-17
- **Status:** proposed
- **Affected files or instructions:** `src/infinity_army_acquisition/cli.py`,
  corresponding HTTP tests, and `README.md`.
- **Observations:** At producer revision
  `098d16c48a07f3b17ff4303e3b237648dfd1b97a`, acquisition reads every response
  body twice and does not retain HTTP validators. Live header-only inspection
  of GET responses from `/army/infinity/en/metadata`, `/army/units/en/101`
  and `/army/units/en/201` found ETags; HEAD responses for metadata and faction
  101 did not expose them. A matching `If-None-Match` returned 304 for metadata,
  but 200 with the same ETag for both sampled faction endpoints. A nonmatching
  validator returned 200 for metadata and faction 101. GET bodies were not
  read or saved by the probe. Some body bytes may still have travelled before
  each connection closed. Other endpoints/languages and the reliability of
  validators across actual upstream edits remain unverified.
- **Proposed improvement:** Add a separately selected advisory check command
  with a language/base-URL/endpoint-specific ETag baseline tied to a known
  snapshot. Use conditional GET where supported; otherwise compare GET
  headers and close the response without reading its body. Check metadata
  and the complete faction endpoint set, including additions/removals; do
  not treat metadata alone as a global data revision. Report changed,
  unchanged-validator, or unknown explicitly; absent validators, errors or
  an unbound baseline must not imply unchanged. Establish initial baseline
  correspondence explicitly rather than deriving opaque ETags from archive
  hashes. Keep check receipts separate from immutable snapshot provenance
  and preserve the full two-pass byte comparison for actual acquisitions.
- **Expected benefit:** Reduce transferred data and avoid unnecessary new
  snapshots when upstream validators match. Savings and change-detection
  reliability are unmeasured; GET-header comparison cannot guarantee zero
  response-body traffic when conditional requests are ignored.
- **Disposition:** Recorded during the user's update-check feasibility
  investigation. Implementation is not authorized by this entry; no CLI or
  snapshot contract changed.

### AI-0003 — Expose standalone acquisition through a bounded agent workflow

- **Date:** 2026-11-25
- **Status:** proposed
- **Affected files or instructions:** `README.md`, package CLI and MCP workspace integration.
- **Observations:** The documented `infinity-army-snapshot` console entry point is
  not exposed by the connected workspace execution tools, which accept tracked
  `tools.*` modules or fixed development profiles. The checkout has no such
  acquisition module. The standalone pytest development-job request also returned
  a validation error; its cause has not been established.
- **Proposed improvement:** Provide a deliberately selected, bounded acquisition
  operation for the existing CLI, with language selection, private output paths,
  and a receipt containing the archive and manifest identities. Keep live network
  acquisition separate from offline tests; verify standalone test-job support.
- **Expected benefit:** Agents can exercise the actual producer and report its
  results without requiring a manual operator command or modifying the consumer.
- **Disposition:** Proposed during the live acceptance investigation. On
  2026-11-25, the separate offline historical inventory successfully ran through
  a tracked `tools.history_inventory` adapter; the standalone pytest job still
  returned `validation_unknown` (both development and pytest test routes).
  Unittest discovery also failed and would not cover the pytest suite.
  Later on 2026-11-25, the tracked `tools.run_checks` adapter successfully ran
  the complete hermetic pytest suite via the asynchronous workspace script
  job (76 passed, 7 subtests passed). Standalone pytest execution is therefore
  available via that adapter; the direct pytest profile failure remains
  unexplained. The proposed live acquisition adapter remains open; no live
  producer contract changed. During historical archive consolidation the
  external bare mirror argument was explicitly rejected with
  `script_path_escape`. Consider a separately authorized read-only source
  mount or import workflow for external bare repositories; retain path
  isolation by default. The archive builder supports a local operator command
  and an explicit partial mode, not a bypass of the workspace restriction.
