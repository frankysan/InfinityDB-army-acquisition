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
