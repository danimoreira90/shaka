# CLAUDE.md — shaka

Rules for any AI coding agent (Claude Code = **CC**) working on this repo.
Read this and `CONTEXT.md` before any work. Architecture: `KICKOFF.md`. Plan: `PLAN.md`.

`AGENTS.md` mirrors these rules for non-Claude agents. If the two ever disagree,
`CLAUDE.md` wins and the mismatch is a bug to fix.

---

## What shaka is

A personal research librarian. You drop in papers and books (PDF/epub you already
own). shaka reads them, indexes them, and answers questions across your library
**with citations** — grounded in your documents, never made up.

Second purpose, equal weight: it is a hands-on tour of the AWS AI Practitioner
(AIF-C01) services. Every feature makes a real AWS service do a real job.

---

## Two Claudes — never say "Claude" bare

There are two. Always disambiguate:

- **CC** — Claude Code, the coding agent building this repo.
- **Bedrock model** — the foundation model shaka *calls at runtime* (Claude/Nova on
  Amazon Bedrock). This is a product dependency, hidden behind a port.

"Ask Claude to summarize" is ambiguous and forbidden. Say "call the Bedrock model"
(runtime) or "CC, implement…" (build time).

---

## Hard Rules (HR)

**HR-1 — Humans commit.** CC never runs `git add`, `git commit`, `git push`, or
`gh pr ...`. CC stages nothing. The human reviews diffs and commits.

**HR-2 — Scope is locked to `PLAN.md`.** No feature outside the current sprint.
**No scraping publishers** (ScienceDirect, IEEE, Elsevier, etc.) — shaka only
processes files the user already holds legitimately. New scope = new ADR first.

**HR-3 — Applied migrations are immutable.** The local audit DB schema is
forward-only. A change is a new timestamped `.sql` file, never an edit to an
applied one. Enforced by SHA-256 stored in `schema_migrations`.

**HR-4 — Don't edit existing tests.** CC may add new test files. CC may not edit
any existing `tests/**/test_*.py` without explicit human approval **and** a
`docs/tech-debt.md` entry recording what changed and why. Never soften, skip, or
`xfail` a test to make a suite green.

**HR-5 — No fake AI, no ungrounded answers.** The keystone rule.
  - (a) Every AI capability calls a real AWS service behind a port, or an explicit
    documented fake. Never a hardcoded string pretending to be a model output.
  - (b) Every answer about the library cites the retrieved chunk(s) it used, or
    plainly says the library does not contain the answer. **No invented citations.
    No claim without a source chunk.**

**HR-6 — Secrets and PII stay out of logs, stdout, and git.** Never commit AWS
credentials. `.env` is gitignored. A document may contain personal data — log a
hash or an ID, never the content. One line in `docs/security-log.md` whenever a
feature first touches document content.

**HR-7 — Cost guardrail.** Default backend is `local` (free; in-memory or on-disk,
`moto` for AWS in tests). Real AWS fires only when a profile is set. Per-run and
per-day USD caps enforced: warn at 50% and 80%, halt at 100%. Prefer free-tier
paths. Tear down paid resources (OpenSearch, Knowledge Bases) at the end of the
sprint that needs them. Cap values live in `src/shaka/config.py`.

**HR-8 — AWS lives behind ports.** `domain/` and `app/` never import `boto3`.
Only `adapters/aws/*` touches AWS. Choosing `local` vs `aws` is one line at the
composition root (`cli.py`). The same test must pass against both backends — that
is the project's main fitness function.

---

## Protected paths (touch only with human approval + a tech-debt entry)

- `migrations/*.sql` that have been applied (HR-3)
- `tests/**/test_*.py` — existing files (HR-4)
- `evals/**/*.jsonl` — append-only
- `src/shaka/**/prompts.py` — system/grounding prompts (spec + approval)
- `docs/adr/0*.md` — applied decisions

---

## How we work

- **Roles:** the human + the assistant orchestrate; CC writes code. The assistant
  hands CC prompts; the human runs them and the terminal.
- **TDD:** RED (failing test, output shown) → GREEN (minimum code) → REFACTOR →
  human commits the `test:` then `feat:` pair.
- **EDD:** for any AI capability, the eval exists first. Capability pass@3 ≥ 0.90,
  regression pass^3 = 1.00 before ship.
- **Backends:** `local` (free, default, CI-safe) and `aws` (real, gated). Tests
  never hit real AWS — `moto` fakes it.
- **Anti-cheat:** after each task, paste full real output of tests / ruff / pyright
  and the staged diff. A failing test means stop and fix production code, not the
  test.

---

## Stack

Python 3.11+, uv (lockfile committed), `src/shaka/` layout, pydantic v2,
pyright strict, ruff, pytest, `moto` for AWS fakes, boto3 for AWS.
Runtime FM via Amazon Bedrock. Conventional commits.
Language: English everywhere (code, docs, UI) unless a rule here says otherwise.
