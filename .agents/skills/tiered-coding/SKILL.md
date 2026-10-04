---
name: tiered-coding
description: Route substantial engineering work through a Sol/root decision-maker and a Luna worker for bounded, verifiable execution. Use when a task can be decomposed into a clear implementation or investigation packet; keep trivial work local.
---

# Tiered coding workflow

## Roles

The current Sol agent is the root. Sol owns intent, architecture, decomposition, worker assignment, integration, review, replanning, and final correctness. Do not force or switch the root model. If the current root is not Sol, state that limitation and do not impersonate Sol.

Use the real custom role `luna_worker` for delegated execution. Its TOML configuration binds its model. Do not claim that a prompt switches models, substitute a legacy worker with a different model, or dispatch if real Luna routing is unavailable; stop and report the limitation.

Sol makes decisions. Luna executes decisions that have already been made. Optimize cost by keeping judgment with Sol and substantial, safely delegatable execution with Luna; do not push unresolved judgment into Luna to reduce cost. Sol retains understanding of ambiguous or high-entropy problems, architecture, unclear requirements, root causes, difficult debugging, competing strategies, integration, and final correctness. Sol also owns decisions involving APIs, protocols, security, privacy, concurrency, distributed state, schemas, migrations, and invariants.

## Decide what to delegate

Keep trivial tasks local. Delegate worthwhile work when the decisions are already made and the scope is bounded and verifiable. Suitable work includes locating files, symbols, or call sites; answering specific exploration questions; focused implementation; tests; lint, type, or format fixes; mechanical edits or refactors; log analysis; and documentation.

Before dispatch, turn ambiguity and high entropy into a bounded, low-entropy Task Packet. Do not delegate unresolved architecture or ask a worker to choose among competing strategies. Give only the context needed for the packet. Use minimal fresh task context; use `fork_turns=none` when supported.

## Task Packet

Every delegated task must state:

- **Goal** — the concrete result to produce.
- **Scope** — the specific files, symbols, or investigation boundary.
- **Constraints** — decisions and rules the worker must preserve.
- **Acceptance criteria** — observable conditions for completion.
- **Validation** — checks to run and evidence to return.
- **Escalate if** — conditions that require Sol to decide or clarify.

Workers execute the packet as written. They do not expand scope, redesign, decide a new API or security, privacy, concurrency, or schema policy unless the packet explicitly decides it, edit unrelated files, or recursively spawn agents unless root explicitly requests it.

Escalate with `NEEDS_SOL` for wrong assumptions, exceeded scope, architecture or API judgment, ambiguity, a materially different problem, or a new validation issue that requires diagnosis. Report a concrete hypothesis or evidence when possible.

## Parallel work and retries

Run parallel tasks only when their write sets do not overlap and they have no unfinished dependencies. Use a small number of useful workers; avoid coordination overhead.

If Luna returns `BLOCKED` or `NEEDS_SOL`, Sol inspects the evidence, resolves the ambiguity or reasoning problem, and may issue a corrected or narrower Task Packet. Allow at most one retry of the same implementation task; any further attempt requires Sol to supply a concrete new hypothesis or corrected assumptions. Do not retry the same unresolved reasoning problem.

## Result contract

Require each worker to return one status: `DONE`, `BLOCKED`, or `NEEDS_SOL`, followed by:

- Summary
- Files changed
- Validation performed and results
- Unresolved issues
- Required scope expansion, if any

Sol independently inspects the actual diff, scope, important decisions, and acceptance criteria; integrates the result; and runs appropriate final validation. A worker's `DONE` report alone does not establish acceptance.
