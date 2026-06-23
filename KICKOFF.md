# KICKOFF.md — shaka architecture blueprint

**Status:** Draft v0.1
**Read first:** `CLAUDE.md` (rules), `CONTEXT.md` (words). **Tasks live in:** `PLAN.md`.

This doc says *how shaka is shaped* and gives the one recipe every feature follows.
No task list here. If a change doesn't fit this shape, stop and write an ADR.

---

## The shape (hexagonal)

```
            ┌─────────────────────────────────────────────┐
   CLI  ──▶ │  app/   (use cases: ingestion pipeline,      │
 (compose)  │         query path) — pure orchestration     │
            │                                               │
            │  domain/ (models + ports)  ◀── depends on ──┐ │
            └───────────────┬───────────────────────────┘ │
                            │ ports (interfaces)            │
              ┌─────────────┴──────────────┐                │
              ▼                            ▼                 │
        adapters/local/             adapters/aws/            │
        (free, default,             (real AWS, gated)        │
         moto in tests)              boto3 ONLY here ────────┘
```

One rule drives everything (HR-8): **arrows point inward**. `domain/` and `app/`
know nothing about AWS. AWS is a detail behind a port. Swapping `local` ↔ `aws`
changes one line in the composition root, nothing else.

Why this and not "just call boto3 where we need it"? Three payoffs (Ford / Uncle Bob):
- **Free + offline by default.** The `local` adapters run the whole app with no AWS,
  no cost, no creds. That is HR-7 made structural, not a promise.
- **Testable.** Same test runs against `local` and (with `moto`) `aws`. That sameness
  is the project's main fitness function.
- **Evolvable.** Replace the local vector index with OpenSearch by writing one new
  adapter. The pipeline never notices.

---

## Module map

| Path | Holds | May import boto3? |
|---|---|---|
| `src/shaka/domain/models.py` | dataclasses/pydantic: Document, Chunk, Embedding, Query, Answer, Citation | no |
| `src/shaka/domain/ports.py` | Protocols: DocStore, TextExtractor, Chunker, Embedder, VectorIndex, Retriever, Generator, Guardrail | no |
| `src/shaka/app/ingestion.py` | ingestion pipeline use case | no |
| `src/shaka/app/query.py` | query path use case | no |
| `src/shaka/adapters/local/*` | free fakes (in-memory / on-disk) | no |
| `src/shaka/adapters/aws/*` | real AWS adapters | **yes — only here** |
| `src/shaka/audit/*` | local audit DB (service-call log) | no |
| `src/shaka/config.py` | cost caps, chunk knobs, model IDs, backend default | no |
| `src/shaka/cli.py` | composition root: pick backend, wire adapters, run | imports adapters only |

Tests in `tests/` mirror this. Evals in `evals/` (append-only, HR-4).

---

## The two quanta (keep separate — CONTEXT.md)

**Ingestion pipeline** — offline, batch, idempotent:

```python
# app/ingestion.py  (sketch — signatures, not final code)
def ingest(doc_bytes, source, *, extractor, chunker, embedder, index, store) -> IngestionRun:
    # extract → chunk → embed → index; skip if doc_id already present
```

**Query path** — online, per question:

```python
# app/query.py  (sketch)
def answer(question, *, embedder, retriever, generator, guardrail) -> Answer:
    # guard(question) → embed → retrieve top-k → generate grounded → guard(answer)
    # HR-5: Answer carries Citations, or says the library lacks the answer.
```

Both take ports as arguments. Neither knows if a port is `local` or `aws`.

---

## Backend selection (the one switch)

```python
# cli.py  (composition root — the ONLY place that chooses)
def build(backend: str):           # "local" | "aws"
    if backend == "local":
        from shaka.adapters import local as a
    else:
        from shaka.adapters import aws as a
    return Wiring(extractor=a.TextExtractor(), embedder=a.Embedder(), ...)
```

`local` is the default (HR-7). `aws` requires a profile and respects the cost cap.

---

## The recipe — how to add ANY capability

Every feature, every sprint, is the same five steps. This is the heartbeat.

1. **Port.** Add/extend a Protocol in `domain/ports.py`. Tiny — one method.
2. **Test (RED).** Write a test against the *port*, run with the `local` adapter.
   It fails (no impl yet). Paste the red output.
3. **Local adapter (GREEN).** Implement the free fake in `adapters/local/`. Test passes.
4. **AWS adapter.** Implement the real one in `adapters/aws/`. Test it with `moto`
   (still free, still CI-safe). Real AWS only when the human opts in with a profile.
5. **Wire + fitness.** Register both in `cli.py`. The same behavioural test must pass
   on both backends. Human commits `test:` then `feat:`.

Never skip step 2. Never edit an existing test to go green (HR-4) — fix the code.

---

## Audit DB (local CloudTrail)

Every port call that hits AWS (or its fake) writes one `Service Call` row to a local
SQLite/DuckDB file: service, input hash, output hash, est. USD, latency, timestamp.
Never the content (HR-6). This is the evidence trail for HR-5 ("which chunk backed
this claim?") and HR-7 (running cost). Schema changes are forward-only migrations (HR-3).

---

## Sprint 0 target (architecture proof, zero AWS, zero cost)

A thin vertical slice that exercises the whole shape with only `local` adapters:

> Ingest one plain-text document → chunk it → embed with a deterministic local
> embedder → store in an in-memory vector index. Then ask a question → retrieve the
> top chunk → return an Answer that **carries a Citation** (or says "not in your
> library"). End to end, fully tested, runs with `uv run`.

No PDF parsing, no Bedrock, no boto3 yet. The point is to prove ports, the two
quanta, the composition root, and HR-5's citation contract *before* spending a cent
or touching AWS. PDF/Textract, real embeddings, and the Bedrock generator arrive in
Sprint 1+.

**Done when:** `uv run pytest` is green; `uv run shaka ask "..."` returns a grounded
Answer with a Citation against a sample doc; pyright strict and ruff clean.

---

## What this buys the exam

By building this way you will have *touched* (not flash-carded): RAG end to end,
embeddings + vector retrieval, grounding/hallucination control, Bedrock Converse,
Guardrails, S3/Textract/Comprehend/Translate/Polly, managed Knowledge Bases,
agents, and the governance stack — each as a real adapter doing a real job.
